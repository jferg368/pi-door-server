#!/usr/bin/env python3

import logging
import time
import json
import grp
import os
import pwd
from signal import signal, SIGINT, SIGTERM
from sys import exit

from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient
from gpiozero import LED

host = "a30npfuoanec1g-ats.iot.us-west-2.amazonaws.com"
certPath = "/home/pi/iot/"
clientId = "pi_door_opener"
topic = "demo-topic"

# Init AWSIoTMQTTClient
myAWSIoTMQTTClient = None
myAWSIoTMQTTClient = AWSIoTMQTTClient(clientId)
myAWSIoTMQTTClient.configureEndpoint(host, 8883)
myAWSIoTMQTTClient.configureCredentials("{}aws-root-cert.pem".format(certPath), "{}f374a97ce4-private.pem.key".format(certPath), "{}f374a97ce4-certificate.pem.crt".format(certPath))

#GPIO config
door = LED(18)
red = LED(4)
blue = LED(17)
yellow = LED(22)

# AWSIoTMQTTClient connection configuration
myAWSIoTMQTTClient.configureAutoReconnectBackoffTime(1, 32, 20)
myAWSIoTMQTTClient.configureOfflinePublishQueueing(-1)  # Infinite offline Publish queueing
myAWSIoTMQTTClient.configureDrainingFrequency(2)  # Draining: 2 Hz
myAWSIoTMQTTClient.configureConnectDisconnectTimeout(10)  # 10 sec
myAWSIoTMQTTClient.configureMQTTOperationTimeout(5)  # 5 sec
myAWSIoTMQTTClient.connect()

#Currently borrowed from Approximate Engineering example: https://approximateengineering.org/2017/04/running-python-as-a-linux-service/

def drop_privileges(uid_name='nobody', gid_name='nogroup'):
    if os.getuid() != 0:
        # We're not root so, like, whatever dude
        return

    # Get the uid/gid from the name
    running_uid = pwd.getpwnam(uid_name).pw_uid
    running_gid = grp.getgrnam(gid_name).gr_gid
    # Reset group access list
    os.initgroups(uid_name, running_gid)
    # Try setting the new uid/gid
    os.setgid(running_gid)
    os.setuid(running_uid)
    # Ensure a very conservative umask
    old_umask = os.umask(077)

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

# Do anything you need to do before changing to the 'pi' user (our service
# script will run as root initially so we can do things like bind to low
# number network ports or memory map GPIO pins)
# Become 'pi' to avoid running as root

drop_privileges(uid_name='pi', gid_name='pi')

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


myAWSIoTMQTTClient.subscribe('demo-topic', 0, callback)

#Sit around forever and wait for connections
while True:
    pass
