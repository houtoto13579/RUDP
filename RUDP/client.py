from socket import *
from select import select
import collections
import argparse
import logging
from datetime import datetime


udp_data_port = 18888
udp_missing_port = 18889

metadata_size = 16
block_size = 1024
udp_receive_size = block_size + metadata_size

check_missing_cnt = 50

def receive_udp():
    data_dict = {}
    final_data = bytearray()
    data = bytearray()
    s = socket(AF_INET, SOCK_DGRAM)
    s.bind(('localhost', udp_data_port))
    
    counter = 1
    while True:
        if counter%check_missing_cnt == 0:
            final_data += check_missing(data_dict)
        payload, addr = s.recvfrom(udp_receive_size)
        if payload == b'':
            logging.debug('UDP end recv')
            s.close()
            break
        start = int.from_bytes(payload[0:4], 'little')
        data = payload[16:]
        data_dict[start] = data
        counter += 1
    return data_dict

def create_udp_socket():
    s = socket(AF_INET, SOCK_DGRAM)
    s.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    return s

def check_missing(data_dict):
    id_ptr = 0
    final_data = bytearray()
    for id, block in sorted(data_dict.items()):
        #print(id)
        while id_ptr < id:
            print('data miss at id: {}'.format(id_ptr))
            id_ptr += 1
        final_data += block
        id_ptr += 1
    return final_data

def missing_udp_send(ids):
    s = create_udp_socket()
    for id in ids:
        s.sendto(id, (args.host, udp_missing_port))
        # send here

if __name__ == '__main__':
    print("waiting the packet")
    data = receive_udp()
    #print(data[1])