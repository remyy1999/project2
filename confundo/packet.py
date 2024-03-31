import struct

class Packet:
    HEADER_FORMAT = "!LLHHBBB"  # Format string for struct.pack

    def __init__(self, seqNum=0, ackNum=0, connId=0, isSyn=False, isFin=False, isAck=False, payload=b""):
        self.seqNum = seqNum
        self.ackNum = ackNum
        self.connId = connId
        self.isSyn = isSyn
        self.isFin = isFin
        self.isAck = isAck
        self.payload = payload

    def encode(self):
        header = struct.pack(Packet.HEADER_FORMAT,
                             self.seqNum,
                             self.ackNum,
                             self.connId,
                             0,  # Not Used (13 bits)
                             int(self.isAck) << 2 | int(self.isSyn) << 1 | int(self.isFin))  # A|S|F bits
        return header + self.payload

    @classmethod
    def decode(cls, data):
        seqNum, ackNum, connId, _, flags = struct.unpack(Packet.HEADER_FORMAT, data[:12])
        isAck = bool(flags & 0b100)
        isSyn = bool(flags & 0b010)
        isFin = bool(flags & 0b001)
        payload = data[12:]
        return cls(seqNum, ackNum, connId, isSyn, isFin, isAck, payload)

