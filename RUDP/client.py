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
udp_missing_client_port = 18890
udp_missing_server_port = 18889

# percentage
drop_rate = 0.00

tcp_data_port_test = 16667

metadata_size = 8
block_size = 65472
udp_receive_size = block_size + metadata_size

tcp_buffer_size = 2048

check_missing_cnt = 100

parser = argparse.ArgumentParser()
parser.add_argument('--host', default='localhost')
parser.add_argument('-o', '--output', default='output.txt')
parser.add_argument('-t', '--type', default='udp')
args = parser.parse_args()

class client:
    def __init__(self):
        self.final_dict = collections.OrderedDict()
        self.id_ptr = 1
        self.pre_end = 0
        self.missing_buffer = Queue()
        self.recv_thread = Thread(target=self.receive_udp)
        self.missing_send_thread = Thread(target=self.missing_udp_send)
        self.missing_recv_thread = Thread(target=self.missing_udp_recv)
        self.check_thread = Thread(target=self.check_all_recv)
        self.isEnd = False

    def run(self):
        if args.type == 'udp': 
            print("start recv_thread")
            self.recv_thread.start()
            self.missing_recv_thread.start()
            
            time.sleep(10)
            print("start missing_send_thread")
            self.missing_send_thread.start()

            #self.check_thread.start()


            self.recv_thread.join()
            self.missing_recv_thread.join()
            self.missing_send_thread.join()
            return self.build_file()
            #self.check_all_recv.join()
        else:
            return self.receive_tcp()


        
    
    def receive_udp(self):
        print("start listening")
        data_dict = {}
        data = bytearray()
        s = socket(AF_INET, SOCK_DGRAM)
        s.bind(('localhost', udp_data_port))
        
        counter = 1
        while True:
            #if counter%check_missing_cnt == 0:
            #    self.check_missing(data_dict)
            #    data_dict = {}

            payload, addr = s.recvfrom(udp_receive_size)

            if payload == b'':
                #logging.debug('UDP end recv')
                self.check_missing(data_dict)
                print('UDP end recv')
                s.close()
                # TODO: Or initiate count down here
                time.sleep(5)
                self.isEnd = True
                break
            
            id = int.from_bytes(payload[0:4], 'little')

            #start = int.from_bytes(payload[4:8], 'little')
            data_dict[(id, 0)] = payload[metadata_size:]
            counter += 1

    def receive_tcp(self):
        print("tcp reciver")
        data = bytearray()
        s = socket(AF_INET, SOCK_STREAM)
        s.connect((args.host, tcp_data_port_test))
        while True:
            chunk = s.recv(udp_receive_size)
            data += chunk
            if chunk == b'':
                s.close()
                break
        print("size of data", len(data))
        return data

    def check_missing(self, data_dict):
        sorted_data_dict = sorted(data_dict.items())
        for (id,start), block in sorted_data_dict:
            #print(id, start)
            #print(id)
            while self.id_ptr < id:
                print('data miss at id: {}'.format(self.id_ptr))
                self.missing_buffer.put(self.id_ptr)
                self.final_dict[self.id_ptr] = b'\x00' * (block_size)
                self.id_ptr += 1
                #self.pre_end += block_size

            self.final_dict[self.id_ptr] = block
            self.id_ptr += 1

    def missing_udp_send(self):
        #print("start missing send thread")
        s = socket(AF_INET, SOCK_DGRAM)
        s.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        while True:
            while not self.missing_buffer.empty():
                missing_id = self.missing_buffer.get()
                print("send missing id", missing_id)
                s.sendto((missing_id).to_bytes(4, byteorder='little'), (args.host, udp_missing_server_port))
            if self.isEnd:
                s.sendto(b'', (args.host, udp_missing_server_port))
                break

    def missing_udp_recv(self):
        #print("start missing recv thread")
        s = socket(AF_INET, SOCK_DGRAM)
        s.bind(('localhost', udp_missing_client_port))
        while True:
            payload, addr = s.recvfrom(udp_receive_size)
            if payload == b'':
                print('end missing recv thread')
                self.isEnd = True
                s.close()
                break
            id = int.from_bytes(payload[0:4], 'little')
            print("recv missing id", id)
            data = payload[metadata_size:]
            self.final_dict[id] = data 

    def check_all_recv(self):
        while True:
            time.sleep(1)
            #print(self.final_dict.keys())
            if list(self.final_dict.keys()) == list(range(431)) and all(self.final_dict.values()):
                for k, v in self.final_dict.items():
                    print(v)
                break
    def build_file(self, isVideo=False):
        print('create output file with len:' , len(self.final_dict))
        data = bytearray()
        if not isVideo:
            self.id_ptr = 0
            for id in range(len(self.final_dict)):
                data += self.final_dict[id+1]
                self.id_ptr += 1
        return data

if __name__ == '__main__':
    c = client()
    data = c.run()
    with open(args.output, 'wb') as f:
        f.write(data)
