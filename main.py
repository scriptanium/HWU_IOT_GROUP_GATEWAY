#!/usr/bin/env python3

import configparser
import json
import paho.mqtt.client as mqtt
import serial
import sys
import time

mqtt_broker_connected = False
subscribe_topic = "#"
sub_msg = "enable"
refresh_rate = 0

class Config:
    def __init__(self, file):
        self.__config = configparser.ConfigParser()
        self.__config.read(file)
        self.serialports = self.__config.get("SERIAL", option="serialports", fallback="/dev/ttyUSB0").split(",")
        self.speed = self.__config.getint("SERIAL", option="speed", fallback=115200)
        self.timeout = self.__config.getfloat("SERIAL", option="timeout", fallback=0.5)
        self.publish_topic = self.__config.get("MQTT", option="publish_topic", fallback="unknown/unknown")
        self.subscribe_topic = self.__config.get("MQTT", option="subscribe_topic", fallback="unknown/unknown")
        global subscribe_topic
        subscribe_topic = self.subscribe_topic
        self.qos = self.__config.getint("MQTT", option="qos", fallback=1)
        self.port = self.__config.getint("MQTT", option="port", fallback=1883)
        self.address = self.__config.get("MQTT", option="address", fallback="test.mosquitto.org")
        self.ca_cert = self.__config.get("MQTT", option="ca_cert", fallback=None)
        self.cert = self.__config.get("MQTT", option="cert", fallback=None)
        self.key = self.__config.get("MQTT", option="key", fallback=None)
        self.username = self.__config.get("MQTT", option="username", fallback=None)
        self.password = self.__config.get("MQTT", option="password", fallback=None)
        self.auth = {"username": self.username, "password": self.password} if self.username and self.password else None

def on_connect(client: mqtt.Client, userdata, flags, rc):
    _ = client
    _ = userdata
    _ = flags

    if rc == 0:
        print("Connected to mqtt broker")
        global mqtt_broker_connected
        mqtt_broker_connected = True
        client.subscribe(subscribe_topic)
    else:
        print("Failed to connect to mqtt broker")

def on_message(client: mqtt.Client, userdata, msg):
    _ = client
    _ = userdata

    global refresh_rate
    global sub_msg
    try:
        if msg.payload == b"enable" or msg.payload == b"disable":
            sub_msg = str(msg.payload, "ascii")
            print("Service " + sub_msg + "d", sep="")
            return
        tmp = int(msg.payload)
        if tmp < 0 or tmp > 86400: # day in secs
            print("Time not in 1 sec to 1 day range")
            return
        refresh_rate = tmp
        print("Refresh rate changed to " + str(tmp) + " secs")
    except:
        print("Error while getting refresh rate in secs")

def main(config: Config):
    client = mqtt.Client("Gateway", clean_session=True, userdata=None, protocol=mqtt.MQTTv311, reconnect_on_failure=True)
    client.on_connect = on_connect
    client.on_message = on_message
    if config.ca_cert != None and config.cert != None and config.key != None:
        client.tls_set(certfile=config.cert, keyfile=config.key)
    elif config.ca_cert != None:
        client.tls_set(ca_certs=config.ca_cert)
    client.connect(config.address, port=config.port, keepalive=25)
    client.loop_start()

    while mqtt_broker_connected == False:
        print("Trying to connect to mqtt broker")
        time.sleep(1)

    ports = []
    clocks = []
    for srp in config.serialports:
        ports.append(serial.Serial(srp, config.speed, timeout=config.timeout))
        clocks.append(time.time())
    try:
        while True:
            p: serial.Serial
            for i, p in enumerate(ports):
                line = p.readline()
                if line != b"" and sub_msg == "enable" and time.time() - clocks[i] > refresh_rate:
                    clocks[i] = time.time()
                    try:
                        val = int(line)
                    except ValueError:
                        continue
                    if val == 200:
                        print("Bridge on port {} just came up".format(config.serialports[i]))
                    elif val == 100:
                        print("Bridge on port {} has esp-now connectivity errors".format(config.serialports[i]))
                    else:
                        tmp = time.time()
                        print("Button on board {:d} pressed on {}".format(val, time.ctime(tmp)))
                        client.publish(
                            config.publish_topic,
                            json.dumps({"board" : val, "date": tmp}),
                            config.qos,
                            retain=False
                        )
    except KeyboardInterrupt:
        client.disconnect()
        client.loop_stop()
        return

if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(-1)
    if sys.argv[1] == "-h":
        print("USAGE\n\t",
            sys.argv[0] + " -h\t\tThis help\n\t",
            sys.argv[0] + " config.ini\tLoad config file and run",
        )
        sys.exit(0)
    main(Config(sys.argv[1]))
