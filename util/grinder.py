#!/usr/bin/env python2.7
"""
    compress compiled vm assembly from butcher into pure BeeF assembly
"""
import sys

ASSEMBLY_CHARS = {'_','^','>','<','+','-','[',']'}
COMMENT_DELIM = '#'
LINE_MAX = 80

def main():
    if len(sys.argv) != 3:
        print("usage: grind source_beef_file destination_beef_file")
        exit(1)
    with open(sys.argv[1],'r') as src:
        with open(sys.argv[2],'w') as dest:
            in_directives = True
            char_count = 0
            while True:
                char = src.read(1)
                if not char:
                    break
                if char == COMMENT_DELIM and in_directives:
                    src.readline() # throw out the rest of the line
                elif char in ASSEMBLY_CHARS:
                    if char_count == LINE_MAX:
                        dest.write('\n')
                        char_count = 0
                    dest.write(char)
                    char_count = char_count + 1
            

if __name__ == '__main__':
    main()