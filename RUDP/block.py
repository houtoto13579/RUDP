class block:
    def __init__(self, id, frame, start, end, data, timestamp):
        # block id
        self.id = id
        
        # frame id, might not needed if we use text file for testing
        self.frame = frame 

        # the start position for the frame
        self.start = start

        # the end position for the frame
        self.end = end

        # the timestamp for this block
        self.timestamp = timestamp

        # data
        self.data = data

    def build_meta(self):
        self.metadata = (self.id).to_bytes(4, byteorder='little')
        self.metadata += (self.start).to_bytes(4, byteorder='little')
        #self.metadata += (self.end).to_bytes(4, byteorder='little')
        #self.metadata += (self.timestamp).to_bytes(4, byteorder='little')

    def __repr__(self):
        return str(self.__dict__)