import threading
import time
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
        # Thread
        self.thread = threading.Thread(target=self.run, daemon=True)
        self.thread.start()
        # Events
        self.is_received_data = False
        self.is_transmit_data = False

    def run(self):
        """Continually get messages from a NIOS"""
        with Popen('C:/intelFPGA_lite/18.0/quartus/bin64/nios2-terminal.exe', shell=True, stdout=PIPE) as p: # Path for Windows
        # with Popen("nios2-terminal", shell=True, executable='/bin/bash', stdout=PIPE) as p: # Path for Ubuntu
            for line in p.stdout:
                # Read Data
                nios_data = line.decode().strip()
                if (nios_data == '') or (nios_data[0] == 'n'): # Ignore Empty Line/Lines starting with Nios
                    continue
                nios_data = self._process_data(nios_data)
                nios_data = NiosDataModel(**nios_data)
                self.receive_msg = nios_data
                self.is_received_data = True

                # Write Data
                if self.is_transmit_data:
                    p.stdin.write(str.encode(self.transmit_data))
                    self.is_transmit_data = False
                    
    def send(self, transmit_data):
        """Sets message to send to Nios"""
        self.transmit_data = "$" + transmit_data + "$" #$ Indicates start/end of message character
        self.is_transmit_data = True

    def get(self):
        """Get messages"""
        self.is_received_data = False
        return self.receive_msg

    def _process_data(self, raw_data):
        """Processes raw data from Terminal"""
        arr = raw_data.split(',')
        if len(arr) != 5:
            return
        arr = [int(x, 16) for x in arr]
        coords = [self._twos_comp(x, 32)/8388608 for x in arr[:3]]
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

    def __init__(self, max_queue_size=2):
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


class MQTT(object):
    """Handles MQTT Connections"""

    def __init__(self, client, hostname, port) -> None:
        # Client
        self.client = client
        self.client.on_connect = self.on_connect
        self.client.username_pw_set(username=MQTT_USERNAME, password=MQTT_PASSWORD)
        self.client.tls_set(MQTT_CA_CERT, MQTT_CERTFILE, MQTT_KEYFILE, tls_version=2)
        self.is_connected = False
        # Server
        self.hostname, self.port = hostname, port

    def connect(self):
        """Connects to MQTT Server"""
        while not self.is_connected:
            try:
                self.client.connect(self.hostname, self.port)
                self.client.loop_start()
            except:
                time.sleep(1)

    def publish(self, topic, payload):
        """Publishes payload to dedicated topic"""
        self.client.publish(topic, payload)

    def on_connect(self, client, userdata, flags, rc):
        """Successful connection callback"""
        if rc == 0:
            self.is_connected = True
