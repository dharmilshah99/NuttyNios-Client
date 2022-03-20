import threading
import time
from subprocess import Popen, PIPE
from collections import deque


from models import *
from config import *

###
# FPGA
###

def fpga_send_game_mode(nios_stream, game_mode_data):
    """Sends game mode to Nios"""
    if game_mode_data == "0":
        nios_stream.send("-")
    elif game_mode_data == "1":
         nios_stream.send("+")
    else:
        return

def fpga_send_score(nios_stream, score_data):
    """sends score for Nios to Display"""
    nios_stream.send("$Score" + score_data)

def fpga_get_direction(direction_data):
    """Gets direction to send to Nios"""
    # Get first direction
    if direction_data.directions_moved:
        direction_moved = direction_data.directions_moved.pop()
        return direction_moved

def fpga_send_direction(nios_stream, direction_moved):
    """Sends direction to Nios"""
    # Return
    if direction_moved == DirectionMoved.UP:
        nios_stream.send("~UP")
    elif direction_moved == DirectionMoved.DOWN:
        nios_stream.send("~DOWN")
    elif direction_moved == DirectionMoved.LEFT:
        nios_stream.send("~LEFT")
    elif direction_moved == DirectionMoved.RIGHT:
        nios_stream.send("~RIGHT")
    else:
        nios_stream.send(None)
    return

def fpga_process_data(raw_data):
    """Processes raw data from Terminal"""
    arr = raw_data.split(',')
    if len(arr) != 5:
        return
    arr = [int(x, 16) for x in arr]
    coords = [fpga_twos_comp(x, 32)/8388608 for x in arr[:3]]
    return {
        "axes": coords,
        "buttons": arr[3],
        "switches": arr[4]
    }

def fpga_twos_comp(val, bits):
    """Interprets integer as 32bit twos-complement number"""
    if (val & (1 << (bits - 1))) != 0:
        val = val - (1 << bits)
    return val


###
# Objects
###

class NiosDataStream(object):
    """Gets data in a dedicated thread"""

    def __init__(self, jtag_client, max_queue_size=3):
        """Initialize Thread."""
        self.jtag_client = jtag_client
        self.message_buffer = deque(maxlen=max_queue_size)
        # Thread
        self.thread = threading.Thread(target=self.run, daemon=True)
        self.thread.start()
        # Events
        self.is_received_data = False        

    def run(self):
        """Continually get messages from a NIOS"""
        while True:
            # Read
            nios_data = self.jtag_client.read()
            nios_data = nios_data.decode()
            # Process
            if (nios_data == '') or (nios_data[0] == 'n'):
                continue
            self.receive_msg = self._process(nios_data)
            if self.receive_msg:
                self.is_received_data = True
                    
    def send(self, transmit_data):
        """Sends message to send to Nios"""
        if transmit_data is not None:
            self.jtag_client.write(str.encode(transmit_data + "$"))  #$ Indicates start/end of message character
            self.is_transmit_data = True

    def get(self):
        """Get messages"""
        self.is_received_data = False
        return self.receive_msg

    def _process(self, data):
        """Returns last valid input of Nios"""
        # Buffer Input
        self.message_buffer.append(data)
        msg = ''.join(self.message_buffer)
        if len(msg) > 1:
            msg = msg.splitlines()[-2]
            return msg
        else:
            return None

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


class MQTT(object):
    """Handles MQTT Connections"""

    def __init__(self, client, hostname, port) -> None:
        # Client
        self.client = client
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.username_pw_set(username=MQTT_USERNAME, password=MQTT_PASSWORD)
        self.client.tls_set(MQTT_CA_CERT, MQTT_CERTFILE, MQTT_KEYFILE, tls_version=2)
        self.is_connected = False
        # Server
        self.hostname, self.port = hostname, port
        # Data
        self.difficulty_data = None
        self.difficulty_received = False
        self.score_data = None
        self.score_received = False
        # Topics
        self.subscribe_topics = [("game/data/difficulty", 0), (f"node/{MQTT_CLIENT_NAME}/data/score", 0)]

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
        client.subscribe(self.subscribe_topics)
    
    def on_message(self, client, userdata, msg):
        """On message callback"""
        # Retrieve Game Difficulty
        if msg.topic == "game/data/difficulty":        
            self.difficulty_data = msg.payload.decode()
            print(f"[INFO] Game mode selected: {self.difficulty_data}")
            self.difficulty_received = True
        # Retreive Score
        if msg.topic == f"node/{MQTT_CLIENT_NAME}/data/score":
            self.score_data = msg.payload.decode()
            print(f"[INFO] Score: {self.score_data}")
            self.score_received = True
    
    def read_message(self, attr_name, attr_name_flag):
        # TODO: Find a more elegant way that doesnt use set/get attributes.
        """Reads message received"""
        if getattr(self, attr_name): 
            setattr(self, attr_name_flag, False)
            return getattr(self, attr_name)
        else:
            return None