import socket
import sys
import struct
import os

try:
    # python urft_server.py <ip> <port>
    UDP_IP = sys.argv[1]
    UDP_PORT = int(sys.argv[2])
except:
    print("Usage: python urft_server.py <ip> <port>")
    exit(2)

class Recipient:
    def __init__(self):
        self.__file_path = ''
        self.__received_buff = {} 
        self.__sock = None
        
    def receive_metadata(self, timeout=2):
        self.__sock.settimeout(timeout)
        while True:
            try:
                data, addr = self.__sock.recvfrom(4096)
                packet_type = data[0]
                seq_num = struct.unpack('!BxxxI', data[:8])[1]
                
                if packet_type == 0x00:
                    raw_filename = data[8:].decode('utf-8').strip('\x00')
                    self.__file_path = os.path.basename(raw_filename)
                    
                    print(f"Received Metadata. Filename: {self.__file_path}") 

                    ack = struct.pack('!BxxxI', 0xFF, seq_num)
                    self.__sock.sendto(ack, addr)
                    
                    self.__sock.settimeout(None)
                    return
                    
            except socket.timeout:
                # waiting for meta bata from client
                pass
                
    def receive_data_with_buffer(self):
        next_expected = 1 
        
        with open(self.__file_path, 'wb') as f:
            while True:
                try: 
                    data, addr = self.__sock.recvfrom(4096)
                    packet_type = data[0]
                    seq_num = struct.unpack('!BxxxI', data[:8])[1]
                    payload = data[8:] 
                    
                    if packet_type == 0x02: # FIN 
                        ack = struct.pack('!BxxxI', 0xFF, seq_num)
                        # self.__sock.sendto(ack, addr)
                        print(f"File '{self.__file_path}' transfer complete!")
                        break

                    elif packet_type == 0x01: # Data
                        ack = struct.pack('!BxxxI', 0xFF, seq_num)
                        # send ack with seq_num
                        self.__sock.sendto(ack, addr)
                        
                        # add to received buff if not expected sequence
                        if seq_num >= next_expected and seq_num not in self.__received_buff:
                            self.__received_buff[seq_num] = payload
                        
                        # if received buff is in correct order write to file
                        while next_expected in self.__received_buff:
                            f.write(self.__received_buff.pop(next_expected))
                            next_expected += 1
                            
                    elif packet_type == 0x00: # re-acked meta data 
                        ack = struct.pack('!BxxxI', 0xFF, 0)
                        self.__sock.sendto(ack, addr)
                        
                except Exception as e:
                    print(f"Error during file transfer: {e}")
                    break
                
    def run(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind((UDP_IP, UDP_PORT))
        self.__sock = sock
        
        self.receive_metadata()
        self.receive_data_with_buffer()
        self.__sock.close()

if __name__  == "__main__":
    recipient = Recipient()
    recipient.run()