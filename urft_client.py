import socket
import sys
import struct
import time
import os
from typing import List

# python urft_client.py <file_path> <ip> <port>
FILE_PATH = sys.argv[1] if len(sys.argv) > 1 else "test.bin"
UDP_IP = sys.argv[2] if len(sys.argv) > 2 else "127.0.0.1"
UDP_PORT = int(sys.argv[3]) if len(sys.argv) > 3 else 5005

class Sender:
    def __init__(self):
        self.__window_size = 1024 
        self.__chunk_size = 1024
        self.__chunks: List[bytes] = []
        self.__sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        
    def read_file(self, file_path):
        try:
            with open(file_path, 'rb') as f:
                while True:
                    data = f.read(self.__chunk_size)
                    if not data:
                        break
                    self.__chunks.append(data)
            print(f"Read '{file_path}': {len(self.__chunks)} chunks prepared.")
            return True
        except FileNotFoundError as e:
            print(f"Error: {e}")
            return False
        
    def create_packet(self, packet_type, seq_num, payload):
        header = struct.pack('!BxxxI', packet_type, seq_num) 
        return header + payload
    
    def send_metadata_with_ack(self, filename, timeout=1.0):
        packet = self.create_packet(0x00, 0, filename.encode('utf-8')) 
        
        self.__sock.settimeout(timeout)
        while True:
            self.__sock.sendto(packet, (UDP_IP, UDP_PORT))
            try:
                ack_packet, _ = self.__sock.recvfrom(8)
                ack_type = ack_packet[0]
                ack_seq = struct.unpack('!BxxxI', ack_packet)[1]
                
                if ack_type == 0xFF and ack_seq == 0:
                    return
            except socket.timeout:
                # timeout pass and send header again
                pass
            
    def send_data_with_window(self, logical_timeout=0.5):
        base = 1 
        next_seq = 1     
        packets_sent = {}
        acked = set()
        total_chunks = len(self.__chunks)
        
        # set little timeout
        self.__sock.settimeout(0.02) 

        while base <= total_chunks:
            # send all data in window
            while next_seq < base + self.__window_size and next_seq <= total_chunks:
                chunk_idx = next_seq - 1 
                packet = self.create_packet(0x01, next_seq, self.__chunks[chunk_idx])
                
                self.__sock.sendto(packet, (UDP_IP, UDP_PORT))
                packets_sent[next_seq] = (packet, time.time())
                next_seq += 1
                
            # wait for ack
            try:
                ack_packet, _ = self.__sock.recvfrom(8)
                ack_type = ack_packet[0]
                ack_seq = struct.unpack('!BxxxI', ack_packet)[1]
                
                if ack_type == 0xFF and ack_seq in packets_sent:
                    del packets_sent[ack_seq]
                    acked.add(ack_seq)
                    
                    # sliding window (Base) to latest ack
                    while base in acked:
                        base += 1
            except socket.timeout:
                pass
            
            # retranmission non-acked packets
            current_time = time.time()
            for seq_num, (packet, timestamp) in list(packets_sent.items()):
                if current_time - timestamp > logical_timeout:
                    self.__sock.sendto(packet, (UDP_IP, UDP_PORT))
                    packets_sent[seq_num] = (packet, current_time)
                    
    def send_fin(self, timeout=1.0):
        fin_seq = len(self.__chunks) + 1 
        packet = self.create_packet(0x02, fin_seq, b'')
        
        self.__sock.settimeout(timeout)
        while True:
            self.__sock.sendto(packet, (UDP_IP, UDP_PORT))
            try: 
                ack_packet, _ = self.__sock.recvfrom(8)
                ack_seq = struct.unpack('!BxxxI', ack_packet)[1]
                if ack_seq == fin_seq:
                    return
            except socket.timeout:
                # retransmition
                pass
        
    def run(self):
        if not self.read_file(FILE_PATH):
            return
            
        start_time = time.time()
        self.send_metadata_with_ack(os.path.basename(FILE_PATH))
        self.send_data_with_window()
        self.send_fin()
        self.__sock.close()
        print(f"Total time taken: {time.time() - start_time:.2f} seconds")
        
if __name__ == "__main__":
    sender = Sender()
    sender.run()