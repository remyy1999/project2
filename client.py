import sys
import socket
import time
import os

from confundo.common import Packet
from confundo.socket import Socket, State

def main():
    if len(sys.argv) != 4:
        sys.stderr.write("ERROR: Usage: python3 client.py <HOSTNAME-OR-IP> <PORT> <FILENAME>\n")
        sys.exit(1)

    hostname = sys.argv[1]
    port = int(sys.argv[2])
    filename = sys.argv[3]

    try:
        file_size = os.path.getsize(filename)
    except FileNotFoundError:
        sys.stderr.write("ERROR: File not found: {}\n".format(filename))
        sys.exit(1)

    try:
        with open(filename, "rb") as file:
            connection_id = 0
            sequence_number = 50000  # Initial sequence number
            acknowledgment_number = 0
            chunk_size = 1000  # Adjust chunk size as needed

            # Open UDP socket and initiate 3-way handshake
            sock = Socket()
            sock.connect((hostname, port))

            # Send SYN packet and expect SYN-ACK
            while True:
                pkt = Packet(seqNum=sequence_number, connId=connection_id, isSyn=True)
                sock._send(pkt)
                response_pkt = sock._recv()
                if response_pkt and response_pkt.isSyn and response_pkt.isAck:
                    connection_id = response_pkt.connId
                    acknowledgment_number = response_pkt.seqNum + 1  # Next expected sequence number
                    break

            # Send file data in chunks
            while True:
                data = file.read(chunk_size)
                if not data:
                    break
                sequence_number += len(data)
                pkt = Packet(seqNum=sequence_number, ackNum=acknowledgment_number, connId=connection_id, isAck=True, payload=data)
                sock._send(pkt)
                acknowledgment_number += len(data)
                # Handle retransmission if needed

            # Send FIN packet
            pkt = Packet(seqNum=sequence_number, ackNum=acknowledgment_number, connId=connection_id, isFin=True)
            sock._send(pkt)

            # Expect ACK for FIN packet
            while True:
                response_pkt = sock._recv()
                if response_pkt and response_pkt.isAck:
                    break

            # Wait for incoming FIN packets
            start_time = time.time()
            while time.time() - start_time < 2:
                response_pkt = sock._recv()
                if response_pkt and response_pkt.isFin:
                    pkt = Packet(seqNum=response_pkt.ackNum, ackNum=response_pkt.seqNum + 1, connId=connection_id, isAck=True)
                    sock._send(pkt)

            # Close connection
            sock.close()
            sys.exit(0)

    except socket.error as e:
        sys.stderr.write("ERROR: {}\n".format(e))
        sys.exit(1)
    except Exception as e:
        sys.stderr.write("ERROR: {}\n".format(e))
        sys.exit(1)

if __name__ == "__main__":
    main()
