import json
import paho.mqtt.client as paho
import intel_jtag_uart

from utils import *
from config import *

###
# Global Variables
###

MQTT_CLIENT = paho.Client(MQTT_CLIENT_NAME)

###
# Main
###

if __name__ == "__main__":
    # Initialize Objects
    JtagClient = intel_jtag_uart.intel_jtag_uart()
    MQTTConnection = MQTT(MQTT_CLIENT, MQTT_HOSTNAME, MQTT_PORT)
    MQTTConnection.connect()
    NiosStream = NiosDataStream(JtagClient)
    DirectionProcessor = ProcessDirection()
    # State Vars
    previous_direction = None
    while True:
        if NiosStream.is_received_data:
            # Process
            data = NiosStream.get()
            data = fpga_process_data(data)
            print(data)
            data = NiosDataModel(**data)
            # Button
            ButtonData = ButtonModel(data.buttons)
            MQTTConnection.publish(topic=f"node/{MQTT_CLIENT_NAME}/data/button", payload=json.dumps(ButtonData.__dict__))
            # Switch
            SwitchData = SwitchModel(data.switches)
            MQTTConnection.publish(topic=f"node/{MQTT_CLIENT_NAME}/data/switch", payload=json.dumps(SwitchData.__dict__))
            # Direction
            DirectionData = DirectionModel(DirectionProcessor(data))
            MQTTConnection.publish(topic=f"node/{MQTT_CLIENT_NAME}/data/direction", payload=json.dumps(DirectionData.__dict__))
            # Publish Direction on CHange
            current_direction = fpga_get_direction(DirectionData)
            if current_direction != previous_direction:
                fpga_send_direction(NiosStream, current_direction)
            previous_direction = current_direction
        else:
            continue
        


###
# Local Testing
###

# if __name__ == "__main__":
#     # Initialize Objects
#     NiosStream = NiosDataStream()
#     DirectionProcessor = ProcessDirection()
#     while True:
#         if NiosStream.events.is_set():
#             data = NiosStream.get()

#             # Button
#             ButtonData = ButtonModel(data.buttons)
#             # print(json.dumps(ButtonData.__dict__))

#             # Switch
#             SwitchData = SwitchModel(data.switches)
#             # print(json.dumps(SwitchData.__dict__))
#             # Direction
#             DirectionData = DirectionModel(DirectionProcessor(data))
#             print(json.dumps(DirectionData.__dict__))
            
#         else:
#             continue
        