#!/usr/bin/env python2.7
import sys

def main():
    if len(sys.argv) != 3:
        print("usage: convert encrypted_message_file path_to_seed_file")
        exit(1)
    with open(sys.argv[1],'r') as src:
        with open(sys.argv[2],'w') as dest:
            for i in range(0,64):
                dest.write("0,")
            dest.write("\n")
            while True:
                char = src.read(1)
                if not char:
                    break
                dest.write("{},".format(str(ord(char))))

if __name__ == '__main__':
    main()