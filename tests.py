from parsers import *
import time
import pdb

MESSAGES = [
        {"id" : 0x284, "data": "0x2000000000000000" },
        {"id" : 0x2b1, "data": "0x0000000000000000" },
        {"id" : 0x2b1, "data": "0x4000000000000000" },
        {"id" : 0x2b1, "data": "0x8000000000000000" },
        {"id" : 0x2b1, "data": "0xc000000000000000" }
        ]

def can_parser_callback(msg):
    print msg

if __name__ == '__main__':
    cp = CANParser(can_parser_callback)
    while True:
        for message in MESSAGES:
          cp._parse(message)
        time.sleep(0.01)

