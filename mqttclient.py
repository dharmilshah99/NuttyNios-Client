import time
import paho.mqtt.client as paho

#define callback
def on_message(client, userdata, message):
    time.sleep(1)
    print("received message =",str(message.payload.decode("utf-8")))

client= paho.Client("client-001") 
# parameters for authetication
client.username_pw_set(username="nuttynios",password="dharmil")
client.tls_set('./certs/server-certs/ca.crt','./certs/client-certs/client.crt','./certs/client-certs/client.key',tls_version=2)

client.on_message=on_message

client.connect('localhost', 1883)
client.loop_start() #start loop to process received messages
print("subscribing ")
client.subscribe("house/bulb1")#subscribe
time.sleep(2)
print("publishing ")
client.publish("house/bulb1","on")#publish
time.sleep(4)
client.disconnect() #disconnect
client.loop_stop() #stop loop