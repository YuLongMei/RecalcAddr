import os, sys
import re

'''
global variances
'''
HEADER_LINES        = 9
INTERVAL_SIZE       = 2
DELIMITER           = ''
FIRST_LINE          = '※' * 20
CONTROL_CODE_BEGIN  = '{'
CONTROL_CODE_END    = '}'
SPLIT_PATTERN       = '(['+CONTROL_CODE_BEGIN+CONTROL_CODE_END+'])'
SINGLE_BYTE_PATTERN = '^[A-Za-z0-9_]*$'

class TextItem:
    def __init__(self):
        self.number = ''
        self.address = 0
        self.length = 0
        self.original = ''
        self.translation = ''

    def __str__(self):
        return self.number\
               + '{:0>8X},{:d}\n'.format(self.address, self.length)\
               + DELIMITER + self.original + DELIMITER\
               + self.translation + DELIMITER

    def calcTranslationLength(self):
        slices = re.split(SPLIT_PATTERN, self.translation[:-1])
        # [0::4]: plain text
        # [1::4]: control code begin
        # [2::4]: control code
        # [3::4]: control code end
        segments = []
        for tup in zip(slices[0::4], [''.join(tup) for tup in \
                                    zip(slices[1::4], slices[2::4], slices[3::4])]):
            segments += list(tup)
        segments.append(slices[-1])
        #print(segments)
        length = 0
        for seg in segments:
            if not seg: continue
            if seg[0] == CONTROL_CODE_BEGIN and seg[-1] == CONTROL_CODE_END:
                #print(int((len(seg))/2-1))
                length += int((len(seg))/2-1)
            elif re.match(SINGLE_BYTE_PATTERN, seg[0]):
                #print(len(seg))
                length += len(seg)
            else:
                #print(len(seg.encode('utf-16-le')))
                length += len(seg.encode('utf-16-le'))
        self.length = length
        #print(self.length)

    def calcAddress(self, pre):
        if pre == None: return
        self.address = pre.address + pre.length + INTERVAL_SIZE

class TextParser:
    def __init__(self):
        self.clean()

    def clean(self):
        self.__header = ''
        self.__contents = []

    def load(self, path):
        try:
            with open(path, 'r', encoding='utf-16-le') as file:
                # Header
                for i in range(HEADER_LINES):
                    line = file.readline()
                    # Stop it in time!
                    if i == 0 and not FIRST_LINE in line:
                        return False
                    self.__header += line

                while True:
                    # Number
                    line = file.readline()
                    if not line:
                        break
                    elif not line.strip():
                        continue

                    item = TextItem()
                    item.number = line

                    # Address, Length
                    line = file.readline()
                    if not line: return False

                    segments = line.split(',')
                    item.address = int(segments[0], 16)
                    item.length = int(segments[1])

                    # Delimiter
                    line = file.readline()
                    if not line: return False
                    global DELIMITER
                    if not DELIMITER: DELIMITER = line

                    # Original
                    while True:
                        line = file.readline()
                        if not line: return False
                        if line == DELIMITER: break
                        item.original += line
                    
                    # Translation
                    while True:
                        line = file.readline()
                        if not line: return False
                        if line == DELIMITER: break
                        item.translation += line

                    self.__contents.append(item)
                    #print(item)
                return len(self.__contents) > 0

        except Exception as e:
            print('Exception occured when reading text "%s": ' \
                  % os.path.basename(file.name) + str(e))
            return False

    def recalculate(self):
        for index, cur in enumerate(self.__contents):
            #print(cur)
            cur.calcTranslationLength()
            if index != 0:
                cur.calcAddress(self.__contents[index-1])
            #print(cur)
            
    def dump(self, path):
        try:
            with open(path, 'w+', encoding='utf-16-le') as file:
                file.write(self.__header)
                for item in self.__contents:
                    file.write(str(item) + '\n\n')
        except Exception as e:
            print('Exception occured when writing text "%s": ' \
                  % os.path.basename(file.name) + str(e))

if __name__ == '__main__':
    command = input('Input "y" to recalculate addresses.\n')
    if command == 'y':
        cur_dir = os.getcwd()
        my_name = os.path.basename(sys.argv[0])
        
        for root, dirs, files in os.walk(cur_dir):
            for file in files:
                if file == my_name:
                    continue
                
                path = os.path.join(root, file)
                parser = TextParser()
                if parser.load(path):
                    parser.recalculate()
                    parser.dump(path)
                    print('Succeeded: {}'.format(path))
                else:
                    print('Failed: {}'.format(path))
