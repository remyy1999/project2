import sys
import socket
import time
import os

from confundo.common import Packet
from confundo.socket import Socket, State

class TCPClient:
    def __init__(self, hostname, port, filename):
        self.hostname = hostname
        self.port = port
        self.filename = filename
        self.sock = Socket()
        self.sequence_number = 50000  # Initial sequence number
        self.acknowledgment_number = 0
        self.connection_id = 0
        self.file_size = 0
        self.chunk_size = 1000  # Adjust chunk size as needed
        self.CWND = 412  # Initial congestion window size
        self.SS_THRESH = 12000  # Initial slow start threshold

    def connect(self):
        try:
            self.file_size = os.path.getsize(self.filename)
        except FileNotFoundError:
            sys.stderr.write("ERROR: File not found: {}\n".format(self.filename))
            sys.exit(1)

        try:
            self.sock.connect((self.hostname, self.port))
            self.initiate_handshake()
            self.send_file()
            self.terminate_connection()
            sys.exit(0)

        except socket.error as e:
            sys.stderr.write("ERROR: {}\n".format(e))
            sys.exit(1)
        except Exception as e:
            sys.stderr.write("ERROR: {}\n".format(e))
            sys.exit(1)

    def initiate_handshake(self):
        # Send SYN packet and expect SYN-ACK
        while True:
            pkt = Packet(seqNum=self.sequence_number, connId=self.connection_id, isSyn=True)
            self.sock._send(pkt)
            response_pkt = self.sock._recv()
            if response_pkt and response_pkt.isSyn and response_pkt.isAck:
                self.connection_id = response_pkt.connId
                self.acknowledgment_number = response_pkt.seqNum + 1  # Next expected sequence number
                break

    def send_file(self):
        with open(self.filename, "rb") as file:
            while True:
                data = file.read(self.chunk_size)
                if not data:
                    break
                self.send_packet(data)

    def send_packet(self, data):
        # Send packet and update sequence number
        pkt = Packet(seqNum=self.sequence_number, ackNum=self.acknowledgment_number, connId=self.connection_id, isAck=True, payload=data)
        self.sock._send(pkt)
        self.sequence_number += len(data)

        # Update congestion window
        if self.CWND < self.SS_THRESH:
            self.CWND += 412
        else:
            self.CWND += (412 * 412) // self.CWND

    def terminate_connection(self):
        # Send FIN packet
        pkt = Packet(seqNum=self.sequence_number, ackNum=self.acknowledgment_number, connId=self.connection_id, isFin=True)
        self.sock._send(pkt)

        # Expect ACK for FIN packet
        while True:
            response_pkt = self.sock._recv()
            if response_pkt and response_pkt.isAck:
                break

        # Wait for incoming FIN packets
        start_time = time.time()
        while time.time() - start_time < 2:
            response_pkt = self.sock._recv()
            if response_pkt and response_pkt.isFin:
                pkt = Packet(seqNum=response_pkt.ackNum, ackNum=response_pkt.seqNum + 1, connId=self.connection_id, isAck=True)
                self.sock._send(pkt)

def main():
    if len(sys.argv) != 4:
        sys.stderr.write("ERROR: Usage: python3 client.py <HOSTNAME-OR-IP> <PORT> <FILENAME>\n")
        sys.exit(1)

    hostname = sys.argv[1]
    port = int(sys.argv[2])
    filename = sys.argv[3]

    client = TCPClient(hostname, port, filename)
    client.connect()

if __name__ == "__main__":
    main()
