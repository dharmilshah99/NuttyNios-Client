import threading
import json
from subprocess import Popen, PIPE
from collections import deque

from models import *
from config import *

###
# Objects
###


class NiosDataStream(object):
    """Gets data in a dedicated thread"""

    def __init__(self):
        """Initialize Thread."""
        self.events = threading.Event()
        self.thread = threading.Thread(target=self.run, daemon=True)
        self.thread.start()

    def run(self):
        """Continually get messages from a NIOS"""
        with Popen('C:/intelFPGA_lite/18.1/quartus/bin64/nios2-terminal.exe', shell=True, stdout=PIPE) as p:
            for line in p.stdout:
                nios_data = line.decode().strip()
                # Ignore Empty Line/Lines starting with Nios
                if (nios_data == '') or (nios_data[0] == 'n'):
                    continue
                # Process
                nios_data = self._process_data(nios_data)
                # print(nios_data)
                nios_data = NiosDataModel(**nios_data)
                self.msg = nios_data
                self.events.set()

    def get(self):
        """Get messages"""
        self.events.clear()
        return self.msg

    def _process_data(self, raw_data):
        """Processes raw data from Terminal"""
        arr = raw_data.split(',')
        if len(arr) != 5:
            return
        arr = [int(x, 16) for x in arr]
        coords = [self._twos_comp(x, 32) for x in arr[:3]]
        return {
            "axes": coords,
            "buttons": arr[3],
            "switches": arr[4]
        }

    def _twos_comp(self, val, bits):
        """Interprets integer as 32bit twos-complement number"""
        if (val & (1 << (bits - 1))) != 0:
            val = val - (1 << bits)
        return val


class ProcessDirection(object):
    """Simple algorithm that processes accelerometer data into directions"""

    def __init__(self, max_queue_size=5):
        """Initialize Queues"""
        self.max_queue_size = max_queue_size
        self.x_tilt_queue = deque(maxlen=self.max_queue_size)
        self.y_tilt_queue = deque(maxlen=self.max_queue_size)

    def __call__(self, nios_data: NiosDataModel):
        """Process into directions"""
        # Process
        x_tilt = self._apply_threshold(
            nios_data.axes[0], RIGHT_TILT_THRESHOLD, LEFT_TILT_THREHOLD, int(DirectionMoved.RIGHT), int(DirectionMoved.LEFT))
        y_tilt = self._apply_threshold(
            nios_data.axes[1], DOWN_TILT_THRESHOLD, UP_TILT_THRESHOLD, int(DirectionMoved.DOWN), int(DirectionMoved.UP))
        # Add to Queue
        self.x_tilt_queue.append(x_tilt)
        self.y_tilt_queue.append(y_tilt)
        # Pop
        ret = []
        self._x_direction_moved = self._pop_queue("x_tilt_queue")
        self._y_direction_moved = self._pop_queue("y_tilt_queue")
        if self._x_direction_moved is not None:
            ret.append(self._x_direction_moved)
        if self._y_direction_moved is not None:
            ret.append(self._y_direction_moved)
        return ret

    def _apply_threshold(self, value, lower_threshold, upper_threshold, return_lower, return_upper):
        """Helper that applies threshold"""
        if value > upper_threshold:
            return return_upper
        elif value < lower_threshold:
            return return_lower
        else:
            return None

    def _pop_queue(self, queue_name):
        """Helper that gets direction from queue"""
        tilt_queue = getattr(self, queue_name)
        if (len(set(tilt_queue)) == 1) and (len(tilt_queue) == self.max_queue_size):
            direction_moved = tilt_queue.pop()
            return direction_moved
        else:
            return None


###
# Helpers
###

def publish_mqtt_topic(mqtt_client, topic_name, payload):
    # Publish
    mqtt_client.publish(
        topic=topic_name,
        payload=payload
    )
    return
