import socket
import sys

UDP_IP = sys.argv[1] if len(sys.argv) > 1 else "127.0.0.1"
UDP_PORT = int(sys.argv[2]) if len(sys.argv) > 2 else 5005
BUFFER_SIZE = 1024 # bytes

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

sock.bind((UDP_IP, UDP_PORT))
print(f"UDP server listening on {UDP_IP}:{UDP_PORT}")

# get file name from client and create new file

# get content of file from client
while True:
    data, addr = sock.recvfrom(BUFFER_SIZE)
    print(f"Received message from {addr}: {data.decode()}")

    # sock.senddto(b"Message Received", addr)
