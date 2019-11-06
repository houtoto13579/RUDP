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

check_missing_cnt = 100

class client:
    def __init__(self):
        self.final_dict = collections.OrderedDict()
        self.id_ptr = 0

    def receive_udp(self):
        data_dict = {}
        final_data = bytearray()
        data = bytearray()
        s = socket(AF_INET, SOCK_DGRAM)
        s.bind(('localhost', udp_data_port))
        
        counter = 1
        while True:
            if counter%check_missing_cnt == 0:
                self.check_missing(data_dict)
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

    def create_udp_socket(self):
        s = socket(AF_INET, SOCK_DGRAM)
        s.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        return s

    def check_missing(self, data_dict):
        sorted_data_dict = sorted(data_dict.items())
        for id, block in sorted_data_dict:
            #print(id)
            while self.id_ptr < id:
                print('data miss at id: {}'.format(self.id_ptr))
                self.final_dict[self.id_ptr] = b''
                self.id_ptr += 1
            self.final_dict[self.id_ptr] = block
            self.id_ptr += 1

    def missing_udp_send(ids):
        s = self.create_udp_socket()
        for id in ids:
            s.sendto(id, (args.host, udp_missing_port))
            # send here

if __name__ == '__main__':
    print("waiting the packet")
    c = client()
    data = c.receive_udp()
    #print(c.final_dict[0])
    #print(c.final_dict[1])