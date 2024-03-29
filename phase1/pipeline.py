from scapy.all import *
from crypt import crypt

import zipfile
import io

import sys
import socket
from datetime import datetime

from time import sleep

from binascii import unhexlify

NSA_SERVER = ('128.114.59.42', 2001)
# NSA_SERVER = ('127.0.0.1', 41257)

try:
    CRUZID = sys.argv[1]
except:
    print('Pass CRUZID as first parameter')
    exit(1)

def get_payload(pcap):
    return rdpcap(pcap)[0].load


def get_crypted_passwd(passwd_pcap):
    crypted_passwd = get_payload(passwd_pcap)
    return crypted_passwd.decode().strip('\n')


def open_listen_socket(port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(('', port))
    sock.listen(1)
    return sock, sock.getsockname() ## return the (ip, port)


def send_crack_passwd_req(crypted_passwd, port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        
        while sock.connect_ex(NSA_SERVER) != 0:
            sleep(1)

        req = "%s 128.114.59.29 %d" % (crypted_passwd, port)
        
        reply = None
        while not reply == 'OK':
            print('Sending "%s"' % req)
            sock.send(req.encode())
        
            reply = sock.recv(10).decode().strip('\n')
            print('Received "%s"' % reply)


def print_time():
    now = datetime.now().time()
    print("\n------ %d:%d:%d" % (now.hour, now.minute, now.second))


def crack_passwd(crypted_passwd):
    listen_sock, (ip, port) = open_listen_socket(51245)

    print_time()
    send_crack_passwd_req(crypted_passwd, port)
    
    sock, _ = listen_sock.accept()

    reply = sock.recv(100).decode()
    
    listen_sock.close()
    sock.close()

    ## reply =  "<crypted_password> <passwd>\n"
    _, passwd = reply.strip('\n').split(' ')

    print('Received passwd = "%s"' % passwd)

    return passwd


def get_obfkey(key_payload, passwd):
    try:
        passwd = passwd.encode()
    except:
        pass
    with zipfile.ZipFile(io.BytesIO(key_payload)) as archive:
        with archive.open('key', pwd=passwd) as key_file:
            key_file_content = key_file.read().decode().strip('\n')
            return key_file_content


def possible_keys(obfkey):
    obfkey = obfkey.strip('\n')
    for s in range(0, len(obfkey)-31, 1):
        yield obfkey[s:s+32]


def decrypt_ciphertext(ciphertext, key, iv):
    cipherfile = 'tmp/ciphertext'
    textfile   = 'tmp/plaintext'

    print(len(ciphertext))
    with open(cipherfile, 'wb') as ct:
        ct.write(ciphertext)

    cmd = 'decryptor/decrypt %s %s %s' % (key, iv, cipherfile)
    print(cmd)

    try:
        proc = subprocess.run(cmd.split(' '))
        assert(proc.returncode == 0)
    except:
        ## When decrypting with the wrong key, the program abort
        return None
    

    with open(textfile, 'rt') as pt:
        return pt.read()


# def load_dict():
#     with open('english_dictionary.txt', 'rt') as d:
#         words = [line.lower() for line in d.readlines()[1:]] ## discard first line comment
#         print('Loaded dictionary of %d words' % len(words))
#         return set(words)


# def makes_sense(msg):
#     # dictionary = ['fluffy', 'fiona', 'unicorns', 'capitol', 'hill', 'bob', 'fiona', 'london', 'bbc', 'washington']
#     dictionary = load_dict()
#     words = msg.lower().split(' ')
    
#     count = 0

#     for word in words:
#         if word in dictionary:
#             count += 1

#     print("hit count = %d" % count)

#     min_hit_number = 0.5 * len(words)
#     return count >= min_hit_number


def get_message(ciphertext, obfkey, iv):

    for key in possible_keys(obfkey):
        print('Trying key "%s"' % key)
        decrypted_msg = decrypt_ciphertext(ciphertext, key, iv)

        # if makes_sense(decrypted_msg):
        if decrypted_msg:
            print('key', key)
            return decrypted_msg


def main():
    passwd_pcap  = 'packets/%s.passwd.pcap'  % CRUZID
    keyzip_pcap  = 'packets/%s.key.zip.pcap' % CRUZID
    message_pcap = 'packets/%s.message.pcap' % CRUZID
    iv_pcap      = 'packets/%s.iv.pcap'      % CRUZID

    # passwd_pcap  = 'fileprof/passwd.pcap'
    # keyzip_pcap  = 'fileprof/key.zip.pcap'
    # message_pcap = 'fileprof/message.pcap'
    # iv_pcap      = 'fileprof/iv.pcap'

    # crypted_passwd = get_crypted_passwd(passwd_pcap)
    # print('crypted_passwd', crypted_passwd)

    # passwd = crack_passwd(crypted_passwd)
    # print('passwd', passwd)

    passwd = "dTRrcA"
    # passwd = 'fluffy'

    obfkey = get_obfkey(get_payload(keyzip_pcap), passwd)
    print('obfkey', obfkey)

    iv = get_payload(iv_pcap).decode().strip('\n')
    print('iv', iv)

    ciphertext = get_payload(message_pcap)

    message = get_message(ciphertext, obfkey, iv)
    print('MESSAGE')
    print(message)

    print('plaintext saved in tmp/plaintext')



main()
