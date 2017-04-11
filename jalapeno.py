#!/usr/bin/python3

import sys
import argparse

# Eventually, this will be the pre-processor

PRE_PROC=('ifdef','else','endif','option','align','equ','=')

class jalapeno:

    def __init__(self):
        print("Nope")

    def reset(self):
        print("Nope")

    def process(self, file_handler):
        print("Nope")

def parse_args():
    parser = argparse.ArgumentParser(description='Description of your program')
    parser.add_argument('-i','--input', help='File to assemble', required=True)

def main(args):
    print("Nope")

if __name__ == '__main__':
    print("Nope")



