import argparse
from datetime import datetime

from block import block
from operator import attrgetter
import time
import collections
import threading 

from socket import socket, AF_INET, SOCK_STREAM, SO_REUSEADDR, SOL_SOCKET, SOCK_DGRAM

block_size = 1024
expireTime = 3

udp_missing_port = 18889
udp_data_port = 18888

q = collections.OrderedDict()

parser = argparse.ArgumentParser()
parser.add_argument('--host', default='localhost')
args = parser.parse_args()

def getBlocks(fileName, step=1024):
    f = open(fileName, "r")
    txt = f.read()
    txt_as_byte = str.encode(txt)
    start = 0
    id = 0
    blocks = []
    length = len(txt)
    for i in range(0, length, step):
        if i + step > length:
            blocks.append(block(id, 0, i, length, txt_as_byte[i:], 0))
        else:
            blocks.append(block(id, 0, i, i+step, txt_as_byte[i:i+step], 0))
        id += 1
        
    return blocks

def create_tcp_socket():
    s = socket(AF_INET, SOCK_STREAM)
    s.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    s.bind((args.host, 16677))
    s.listen(5)
    return s


def create_udp_socket():
    s = socket(AF_INET, SOCK_DGRAM)
    s.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    return s


def send_UDP(blocks):
    isFinished = False
    update_thread = threading.Thread(target=update, args=(lambda: isFinished,))
    update_thread.start()

    missing_thread = threading.Thread()

    s = create_udp_socket()
    for block in blocks:
        block.timestamp = int(datetime.now().strftime('%s'))
        block.build_meta()
        q[block.id] = block
        if block.id != 10 and block.id!=13:
            s.sendto(block.metadata + block.data, (args.host, udp_data_port))
        # send here
    s.sendto(b'', (args.host, udp_data_port))
    print('finish sending')
    isFinished = True
    update_thread.join()

def missing_udp_recv(isFinished):
    data = bytearray()
    s = socket(AF_INET, SOCK_DGRAM)
    s.bind(('localhost', udp_missing_port))
    data_dict = {}
    while True:
        payload, addr = s.recvfrom(udp_receive_size)
        if payload == b'':
            logging.debug('UDP missing end recv')
            s.close()
            break
        
    return data_dict

def update(isFinished):
    while True:
        if isFinished():
            break
        print('update')
        curTime = int(datetime.now().strftime('%s'))
        for key in list(q.keys()):
            if q[key].timestamp >= curTime-expireTime:
                break
            del q[key]
        time.sleep(3)
        

if __name__ == '__main__':
    blocks = getBlocks("data/novel.txt", block_size)
    send_UDP(blocks)

    
    '''
    for block in blocks:
        print(block.data)
        print(block.start)
    '''
    #print (q)
    print('==========')
    #print (q)
    
