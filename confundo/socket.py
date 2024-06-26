# confundo/socket.py

from enum import Enum
import socket
import sys
import time

from .common import *

class State(Enum):
    INVALID = 0
    SYN = 1
    OPEN = 3
    LISTEN = 4
    FIN = 10
    FIN_WAIT = 11
    CLOSED = 20
    ERROR = 21

class Socket:
    '''Confundo socket abstraction'''

    def __init__(self, connId=0, inSeq=None, synReceived=False, sock=socket.socket(socket.AF_INET, socket.SOCK_DGRAM), noClose=False):
        self.sock = sock
        self.connId = connId
        self.sock.settimeout(0.5)
        self.timeout = GLOBAL_TIMEOUT

        self.base = 12345
        self.seqNum = self.base

        self.inSeq = inSeq

        self.lastAckTime = time.time() # last time ACK was sent / activity timer
        self.cc = CwndControl()  # Implement congestion control
        self.outBuffer = b""
        self.inBuffer = b""
        self.state = State.INVALID
        self.nDupAcks = 0

        self.synReceived = synReceived
        self.finReceived = False

        self.remote = None
        self.noClose = noClose

    def connect(self, endpoint):
        remote = socket.getaddrinfo(endpoint[0], endpoint[1], family=socket.AF_INET, type=socket.SOCK_DGRAM)
        (family, type, proto, canonname, sockaddr) = remote[0]

        return self._connect(sockaddr)

    def bind(self, endpoint):
        if self.state != State.INVALID:
            raise RuntimeError()

        remote = socket.getaddrinfo(endpoint[0], endpoint[1], family=socket.AF_INET, type=socket.SOCK_DGRAM)
        (family, type, proto, canonname, sockaddr) = remote[0]

        self.sock.bind(sockaddr)
        self.state = State.LISTEN

    def _connect(self, remote):
        self.remote = remote

        if self.state != State.INVALID:
            raise RuntimeError("Trying to connect, but socket is already opened")

        self.sendSynPacket()
        self.state = State.SYN

        self.expectSynAck()

    def sendSynPacket(self):
        synPkt = Packet(seqNum=self.seqNum, connId=self.connId, isSyn=True)
        self.seqNum += 1
        self._send(synPkt)

    def expectSynAck(self):
        startTime = time.time()
        while True:
            pkt = self._recv()
            if pkt and pkt.isAck and pkt.ackNum == self.seqNum:
                self.base = self.seqNum
                self.state = State.OPEN
                break
            if time.time() - startTime > SYN_WAIT_TIME:
                self.state = State.ERROR
                raise RuntimeError("timeout")

    def close(self):
        if self.state != State.OPEN:
            raise RuntimeError("Trying to send FIN, but socket is not in OPEN state")

        self.sendFinPacket()
        self.state = State.FIN

        self.expectFinAck()

    def sendFinPacket(self):
        finPkt = Packet(seqNum=self.seqNum, connId=self.connId, isFin=True)
        self.seqNum += 1
        self._send(finPkt)

    def expectFinAck(self):
        startTime = time.time()
        while True:
            pkt = self._recv()
            if pkt and pkt.isAck and pkt.ackNum == self.seqNum:
                self.base = self.seqNum
                self.state = State.CLOSED
                break
            if time.time() - startTime > FIN_WAIT_TIME:
                return

    def send(self, data):
        if self.state != State.OPEN:
            raise RuntimeError("Trying to send data, but socket is not in OPEN state")

        self.outBuffer += data

        startTime = time.time()
        while len(self.outBuffer) > 0:
            toSend = self.outBuffer[:MTU]
            pkt = Packet(seqNum=self.seqNum, connId=self.connId, payload=toSend)
            self.seqNum += len(toSend)
            self._send(pkt)

            pkt = self._recv()  
            if pkt and pkt.isAck:
                self.outBuffer = self.outBuffer[len(toSend):]
                self.base = self.seqNum

            if time.time() - startTime > GLOBAL_TIMEOUT:
                self.state = State.ERROR
                raise RuntimeError("timeout")

        return len(data)

    def _send(self, packet):
        if self.remote:
            self.sock.sendto(packet.encode(), self.remote)
        else:
            self.sock.sendto(packet.encode(), self.lastFromAddr)

    def _recv(self):
        try:
            (inPacket, self.lastFromAddr) = self.sock.recvfrom(1024)
        except socket.error as e:
            return None

        inPkt = Packet().decode(inPacket)

        outPkt = None
        if inPkt.isSyn:
            if inPkt.connId != 0:
                self.connId = inPkt.connId
            self.synReceived = True

            outPkt = Packet(seqNum=self.seqNum, ackNum=self.inSeq, connId=self.connId, isAck=True)

        elif inPkt.isFin:
            if self.inSeq == inPkt.seqNum:
                self.finReceived = True

            outPkt = Packet(seqNum=self.seqNum, ackNum=self.inSeq, connId=self.connId, isAck=True)

        elif len(inPkt.payload) > 0:
            if not self.synReceived:
                raise RuntimeError("Receiving data before SYN received")

            if self.finReceived:
                raise RuntimeError("Received data after getting FIN (incoming connection closed)")

            if self.inSeq == inPkt.seqNum:
                self.inBuffer += inPkt.payload

            outPkt = Packet(seqNum=self.seqNum, ackNum=self.inSeq, connId=self.connId, isAck=True)

        if outPkt:
            self._send(outPkt)

        return inPkt
