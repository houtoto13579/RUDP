from socket import *
from select import select
import collections
import argparse
import logging
from datetime import datetime
from threading import Thread
from queue import Queue
from copy import deepcopy
import time 
udp_data_port = 18888
udp_missing_send_port = 18889
udp_missing_recv_port = 18890

metadata_size = 16
block_size = 1024
udp_receive_size = block_size + metadata_size

check_missing_cnt = 100

parser = argparse.ArgumentParser()
parser.add_argument('--host', default='localhost')
args = parser.parse_args()

class client:
    def __init__(self):
        self.final_dict = collections.OrderedDict()
        self.id_ptr = 0
        self.missing_buffer = Queue()
        self.recv_thread = Thread(target=self.receive_udp)
        self.missing_send_thread = Thread(target=self.missing_udp_send)
        self.missing_recv_thread = Thread(target=self.missing_udp_recv)
        self.check_thread = Thread(target=self.check_all_recv)
        self.isEnd = False

    def run(self):
        print("start recv_thread")
        self.recv_thread.start()
        self.missing_recv_thread.start()
        
        time.sleep(10)
        print("start missing_send_thread")
        self.missing_send_thread.start()

        self.check_thread.start()


        self.recv_thread.join()
        self.missing_recv_thread.join()
        self.missing_send_thread.join()
        
        self.check_all_recv.join()

    def receive_udp(self):
        print("start listening")
        data_dict = {}
        data = bytearray()
        s = socket(AF_INET, SOCK_DGRAM)
        s.bind(('localhost', udp_data_port))
        
        counter = 1
        while True:
            if counter%check_missing_cnt == 0:
                self.check_missing(data_dict)
                data_dict = {}

            payload, addr = s.recvfrom(udp_receive_size)

            if payload == b'':
                #logging.debug('UDP end recv')
                self.check_missing(data_dict)
                print('UDP end recv')
                s.close()
                break

            start = int.from_bytes(payload[0:4], 'little')
            data = payload[16:]
            data_dict[start] = data
            counter += 1


    def check_missing(self, data_dict):
        sorted_data_dict = sorted(data_dict.items())
        for id, block in sorted_data_dict:
            #print(id)
            while self.id_ptr < id:
                print('data miss at id: {}'.format(self.id_ptr))
                self.missing_buffer.put(self.id_ptr)
                self.final_dict[self.id_ptr] = b''
                self.id_ptr += 1

            self.final_dict[self.id_ptr] = block
            self.id_ptr += 1

    def missing_udp_send(self):
        print("start missing send thread")
        s = socket(AF_INET, SOCK_DGRAM)
        s.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        while True:
            while not self.missing_buffer.empty():
                missing_id = self.missing_buffer.get()
                print("send missing id", missing_id)
                s.sendto((missing_id).to_bytes(4, byteorder='little'), (args.host, udp_missing_send_port))

    def missing_udp_recv(self):
        print("start missing recv thread")
        s = socket(AF_INET, SOCK_DGRAM)
        s.bind(('localhost', udp_missing_recv_port))
        while True:
            payload, addr = s.recvfrom(udp_receive_size)
            start = int.from_bytes(payload[0:4], 'little')
            print("recv missing id", start)
            data = payload[16:]
            self.final_dict[start] = data 

    def check_all_recv(self):
        while True:
            time.sleep(1)
            #print(self.final_dict.keys())
            if list(self.final_dict.keys()) == list(range(431)) and all(self.final_dict.values()):
                for k, v in self.final_dict.items():
                    print(v)
                break


if __name__ == '__main__':
    c = client()
    c.run()

