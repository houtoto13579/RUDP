import argparse
from datetime import datetime

from block import block
from operator import attrgetter
import time
import collections
from threading import Thread
from queue import Queue

from socket import socket, AF_INET, SOCK_STREAM, SO_REUSEADDR, SOL_SOCKET, SOCK_DGRAM

block_size = 1024
expireTime = 3

udp_data_port = 18888
udp_missing_send_port = 18890
udp_missing_recv_port = 18889

metadata_size = 16
block_size = 1024
udp_receive_size = block_size + metadata_size


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

class Server:
    def __init__(self, blocks):
        self.blocks = blocks
        self.sending_thread = Thread(target=self.send_UDP, args=(self.blocks,))
        self.missing_recv_thread = Thread(target=self.missing_recv)
        self.missing_send_thread = Thread(target=self.missing_send)
        
        self.update_thread = Thread(target=self.update)
        self.isFinished = False

        self.missing_buffer = Queue()
        self.q = collections.OrderedDict()

    def run(self):
        print("start missing_recv_thread")
        self.missing_recv_thread.start()
        time.sleep(10)

        print("start sending_thread")
        self.sending_thread.start()
        self.update_thread.start()
        self.missing_send_thread.start()

        self.missing_recv_thread.join()
        self.sending_thread.join()
        self.update_thread.join()
        self.missing_send_thread.join()

    def send_UDP(self, blocks):
        s = socket(AF_INET, SOCK_DGRAM)
        s.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)

        for block in blocks:
            block.timestamp = int(datetime.now().strftime('%s'))
            block.build_meta()
            self.q[block.id] = block
            if block.id != 10 and block.id!=13:
                s.sendto(block.metadata + block.data, (args.host, udp_data_port))
            # send here
        s.sendto(b'', (args.host, udp_data_port))
        print('finish sending')
        self.isFinished = True

    def missing_recv(self):
        s = socket(AF_INET, SOCK_DGRAM)
        s.bind(('localhost', udp_missing_recv_port))
        while True:
            payload, addr = s.recvfrom(udp_receive_size)
            missing_block_id = int.from_bytes(payload[0:4], 'little')
            print("recv missing block id", missing_block_id)
            self.missing_buffer.put(missing_block_id)

    def missing_send(self):
        s = socket(AF_INET, SOCK_DGRAM)
        s.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        while True:
            while not self.missing_buffer.empty():
                missing_block_id = self.missing_buffer.get()
                if missing_block_id in self.q:
                    missing_block = self.q[missing_block_id]
                    s.sendto(missing_block.metadata + missing_block.data, (args.host, udp_missing_send_port))

    def update(self):
        while True:
            if self.isFinished:
                break
            print('update')
            curTime = int(datetime.now().strftime('%s'))
            for key in list(self.q.keys()):
                if self.q[key].timestamp >= curTime-expireTime:
                    break
                del self.q[key]
            time.sleep(3)

if __name__ == '__main__':
    print("Generating blocks")
    blocks = getBlocks("data/novel.txt", block_size)
    #send_UDP(blocks)
    print("# of Blocks", len(blocks))
    server = Server(blocks)
    server.run()
    
    
    '''
    for block in blocks:
        print(block.data)
        print(block.start)
    '''
    #print (q)
    print('==========')
    #print (q)
    
