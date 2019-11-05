class segment:
    def __init__(self, id, frame, pos, end, data):
        self.id = id
        self.frame = frame
        self.pos = pos
        self.size = end - pos
        self.data = data
        self.meta = (self.frame.pkt_pos).to_bytes(8, byteorder='little')
        self.meta += (self.frame.pkt_size).to_bytes(8, byteorder='little')
        self.meta += (self.pos).to_bytes(8, byteorder='little')
        self.meta += (self.size).to_bytes(8, byteorder='little')

    def __repr__(self):
        return str(self.__dict__)

class frame:
    def __init__(self):
        self.segs = []

    def __repr__(self):
        return str(self.__dict__)

    def isvideo(self):
        try:
            return self.media_type[0] == 'v'
        except AttributeError:
            return False

    def isaudio(self):
        try:
            return self.media_type[0] == 'a'
        except AttributeError:
            return False

    def isPframe(self):
        return self.isvideo() and self.pict_type =='P'

    def isIframe(self):
        return self.isvideo() and self.pict_type == 'I'

    def isBframe(self):
        return self.isvideo() and self.pict_type == 'B'

    def size(self):
        return self.pkt_size

    def make_segs(self, data, step):
        end_pos = self.pkt_pos + self.pkt_size
        sid = 0
        for i in range(self.pkt_pos, end_pos, step):
            if i + step > end_pos:
                self.segs.append(
                    segment(sid, self, i, end_pos, data[i:end_pos]))
            else:
                self.segs.append(
                    segment(sid, self, i, i + step, data[i:i + step]))
            sid += 1