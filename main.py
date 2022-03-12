import json
import paho.mqtt.client as paho

from utils import *
from config import *

###
# Global Variables
###

MQTT_CLIENT = paho.Client(MQTT_CLIENT_NAME)
MQTT_CLIENT.connect(MQTT_HOSTNAME, MQTT_PORT)

###
# Main
###

if __name__ == "__main__":
    NiosStream = NiosDataStream()
    DirectionProcessor = ProcessDirection()
    while True:
        if NiosStream.events.is_set():
            # Get and Process Data
            data = NiosStream.get()
            directions_moved = DirectionProcessor(data)
            # Serialize Data
            SwitchData = SwitchModel(data.switches)
            ButtonData = ButtonModel(data.buttons)
            DirectionData = DirectionModel(directions_moved)
            # Publish
            publish_mqtt_topic(MQTT_CLIENT, f"node/{MQTT_CLIENT_NAME}/data/button", json.dumps(ButtonData.__dict__))
            publish_mqtt_topic(MQTT_CLIENT, f"node/{MQTT_CLIENT_NAME}/data/switch", json.dumps(SwitchData.__dict__))
            publish_mqtt_topic(MQTT_CLIENT, f"node/{MQTT_CLIENT_NAME}/data/direction", json.dumps(DirectionData.__dict__))
        else:
            continue
        