#!/usr/bin/env python2.7
import sys
import os

BYTE_WIDTH = 8
ENC_OFFSET = 64
SEED_EXT  = ".seed"

def bin_n(n,width):
    raw = bin(n)[2:]
    return ''.join(["0"*(width-len(raw)),raw])

def ascii_binarize(c):
    return bin_n(ord(c),BYTE_WIDTH)

def binarize_message_file(source,target,offset):
    with open(source,'r') as src:
        with open(target,'w') as dest:
            for i in range(0,offset):
                dest.write(bin_n(0,BYTE_WIDTH))
                dest.write('\n')
            while True:
                char = src.read(1)
                if not char:
                    break
                dest.write(ascii_binarize(char))
                dest.write('\n')

def make_seedfile_path(source,target):
    target_name = os.path.splitext(os.path.basename(source))[0]
    return target + target_name + SEED_EXT

def main():
    if len(sys.argv) != 3:
        print("usage: convert encrypted_message_file path_to_seed_file")
        exit(1)
    source = sys.argv[1]
    target = sys.argv[2]
    if os.path.isdir(source) and os.path.isdir(target):
        for file in os.listdir(source):
            source_path = source+file
            if not os.path.isfile(source_path):
                continue
            print("Converting: {}".format(source_path))
            target_path = make_seedfile_path(source_path,target)
            binarize_message_file(source_path,target_path,ENC_OFFSET)
    elif os.path.isfile(source):
        if os.path.isfile(target):
            binarize_message_file(source,target,ENC_OFFSET)
        elif os.path.isdir(target):
            target_path = make_seedfile_path(source,target)
            binarize_message_file(source,target_path,ENC_OFFSET)
    else:
        print("Error: {} is a directory, {} is a file".format(source,target))
    


if __name__ == '__main__':
    main()