# Suppress scapy warning regarding ipv6
# https://stackoverflow.com/questions/24812604/hide-scapy-warning-message-ipv6
import logging
logging.getLogger("scapy.runtime").setLevel(logging.ERROR)

from scapy.all import *
from crypt import crypt

import zipfile
import io
import time
import os
import re

import sys
import socket
from datetime import datetime

from time import sleep


MAX_SIZE = 10000

ROUTER = ('128.114.59.42', 5001)


def dump_packet(packet, timestamp, idx):
    with open('capture_folder/%s/passwd%07d.pcap' % (timestamp, idx), 'wb') as p:
        p.write(packet)


def make_timestamp():
    ## DayOfMonth_HH.MM[am|pm]
    return datetime.now().strftime("%d_%I.%M%p").lower()


def extract_crypted(payload, re_pat):    
    m = re_pat.search(payload)
    passwd = m.group('passwd')
    print(passwd.decode())
    return passwd.decode()


def inspects(packets, passwd_file, re_pat):
    for packet in packets:
        packet = Ether(packet)
        if packet and hasattr(packet, "load"):
            crypted = extract_crypted(packet.load, re_pat)
            passwd_file.write(crypted + '\n')
            passwd_file.flush()
            os.fsync(passwd_file.fileno())
        else:
            print("="*15)
            print('NO ATTR LOAD for packet')
            print(packet)
            print("="*15)

        
def capture():

    timestamp = make_timestamp()

    # os.system('mkdir passwds/')

    ## compile pattern to extract passwds
    pat = ''.join(chr(x) for x in range(32, 127))
    pat = re.escape(pat.encode())
    re_pat = re.compile(b".*(?P<passwd>[" + pat + b"]{13}).*")

    passwd_file = open('capture_folder/passwds%s' % timestamp, 'wt')
    
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        
        while sock.connect_ex(ROUTER) != 0:
            sleep(1)

        i = 0
        try:

            packets = []
            while True:
                ## Capture all packets
                print('Waiting packet #%d' % i)            

                ## TODO might read more than one at the same time?
                packet = sock.recv(MAX_SIZE)[40:]

                packets.append(packet)

                if len(packets) == 10:
                    inspects(packets, passwd_file, re_pat)
                    packets = []

                # print('Received packet #%d' % i)
                i += 1

        except KeyboardInterrupt:
            passwd_file.close()
            print('\nStop capturing packets')

capture()
