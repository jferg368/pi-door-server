#!/usr/bin/env python3

import logging
import configparser
import time
import json
import grp
import os
import pwd
from signal import signal, SIGINT, SIGTERM
from sys import exit

from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient
from gpiozero import LED


config = configparser.ConfigParser()
config.read('config/pi-door-server.cfg')  # Update to use argparse to read config file options
host = config['Client']['host']
clientId = config['Client']['clientId']
topic = config['Client']['topic']
caFilePath = config['Client']['caFilePath']
keyPath = config['Client']['keyPath']
certificatePath = config['Client']['certificatePath']
port = int(config['Client']['port'])

# Init AWSIoTMQTTClient
piAWSIoTMQTTClient = AWSIoTMQTTClient(clientId)
piAWSIoTMQTTClient.configureEndpoint(host, port)
piAWSIoTMQTTClient.configureCredentials(caFilePath, keyPath, certificatePath)

# AWSIoTMQTTClient connection configuration
offlinePublishQueueing = int(config['MQTT']['offlinePublishQueueing'])
drainingFrequency = int(config['MQTT']['drainingFrequency'])
MQTTOperationTimeout = int(config['MQTT']['MQTTOperationTimeout'])
QoS = int(config['MQTT']['QoS'])

baseReconnectQuietTimeSecond = int(config['Connection']['baseReconnectQuietTimeSecond'])
maxReconnectQuietTimeSecond = int(config['Connection']['maxReconnectQuietTimeSecond'])
stableConnectionTimeSecond = int(config['Connection']['stableConnectionTimeSecond'])

connectDisconnectTimeout = int(config['Connection']['connectDisconnectTimeout'])

piAWSIoTMQTTClient.configureAutoReconnectBackoffTime(
    baseReconnectQuietTimeSecond,
    maxReconnectQuietTimeSecond,
    stableConnectionTimeSecond
    )
piAWSIoTMQTTClient.configureOfflinePublishQueueing(offlinePublishQueueing)
piAWSIoTMQTTClient.configureDrainingFrequency(drainingFrequency)
piAWSIoTMQTTClient.configureConnectDisconnectTimeout(connectDisconnectTimeout)
piAWSIoTMQTTClient.configureMQTTOperationTimeout(MQTTOperationTimeout)
piAWSIoTMQTTClient.connect()


#GPIO config
door = LED(18)
red = LED(4)
blue = LED(17)
yellow = LED(22)



#Currently borrowed from Approximate Engineering example: https://approximateengineering.org/2017/04/running-python-as-a-linux-service/

def get_shutdown_handler(message=None):
    """
    Build a shutdown handler, called from the signal methods
    :param message:
        The message to show on the second line of the LCD, if any. Defaults to None
    """
    def handler(signum, frame):
        # If we want to do anything on shutdown, such as stop motors on a robot,
        # you can add it here.
        print(message)
        exit(0)
    return handler

signal(SIGINT, get_shutdown_handler('SIGINT received'))
signal(SIGTERM, get_shutdown_handler('SIGTERM received'))

def blink(led):
    for x in range(5):
        led.on()
        time.sleep(.5)
        led.off()
        time.sleep(.5)

def callback(client, userdate, message):
    message_json = json.loads(message.payload.decode('utf8').replace("'", '"'))
    led = message_json['led']
    print('Activating!')
    if led == 'red':
        blink(red)
    if led =='blue':
        blink(blue)
    if led =='door':
        door.on()
        time.sleep(1)
        door.off()
    if led == 'multi':
        for i in range(10):
            red.on()
            time.sleep(.25)
            red.off()
            blue.on()
            time.sleep(.25)
            blue.off()
    if led == 'yellow':
        blink(yellow)


piAWSIoTMQTTClient.subscribe('demo-topic', 0, callback)

#Sit around forever and wait for connections
while True:
    pass
