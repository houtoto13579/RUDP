import argparse
from datetime import datetime

from block import block
from operator import attrgetter
import Queue
import time
import collections

from socket import socket, AF_INET, SOCK_STREAM, SO_REUSEADDR, SOL_SOCKET, SOCK_DGRAM

expireTime = 3
q = collections.OrderedDict()

def getBlocks(fileName, step=10):
    f = open(fileName, "r")
    txt = f.read()
    start = 0
    id = 0
    blocks = []
    length = len(txt)
    for i in range(0, length, step):
        if i + step > length:
            blocks.append(block(id, 0, i, length, txt[i:], 0))
        else:
            blocks.append(block(id, 0, i, i+step, txt[i:i+step], 0))
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
    s = create_udp_socket()
    for block in blocks:
        block.timestamp = int(datetime.now().strftime('%s'))
        q[block.id] = block
        time.sleep(1)
        # send here



def update():
    curTime = int(datetime.now().strftime('%s'))
    for key in q:
        if q[key].timestamp >= curTime-expireTime:
            break
        del q[key]
        

if __name__ == '__main__':
    blocks = getBlocks("data/text.txt", 10)
    send_UDP(blocks)
    
    
    for block in blocks:
        print(block.data)
        
    print q
    update()
    print('==========')
    print q
    
