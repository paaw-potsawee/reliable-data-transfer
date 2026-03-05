import socket
import sys

UDP_IP = sys.argv[2] if len(sys.argv) > 1 else "127.0.0.1"
UDP_PORT = int(sys.argv[3]) if len(sys.argv) > 2 else 5005
MESSAGE = sys.argv[1]

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# send file name to server

# send content of file to server
sock.sendto(MESSAGE.encode(), (UDP_IP, UDP_PORT))

sock.close()
