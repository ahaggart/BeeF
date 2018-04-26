#!/usr/bin/env python2.7
"""
    compress compiled vm assembly from butcher into pure BeeF assembly

    also does some late optimization
"""
import sys

ASSEMBLY_CHARS = {'_','^','>','<','+','-','[',']'}
COMPLEMENT = {
    '+':'-',
    '-':'+',
    '>':'<',
    '<':'>',
    '_':'^', # ebut not the other way around
}
COMMENT_DELIM = '#'
LINE_MAX = 80
NEWLINE = '\n'

def chunks(_list, chunk_size):
    for i in xrange(0, len(_list), chunk_size):
        yield _list[i:i + chunk_size]

def main():
    if len(sys.argv) != 3:
        print("usage: grind source_beef_file destination_beef_file")
        exit(1)
    with open(sys.argv[1],'r') as src:
        with open(sys.argv[2],'w') as dest:
            in_directives = True
            line = []
            while True:
                char = src.read(1)
                if not char:
                    break
                if char == COMMENT_DELIM and in_directives:
                    src.readline() # throw out the rest of the line
                elif char in ASSEMBLY_CHARS:
                    # remove cancelling instructions
                    if line and char in COMPLEMENT and line[-1] == COMPLEMENT[char]:
                        line.pop()
                    else:
                        line.append(char)

            lines = []
            for chunk in chunks(line,LINE_MAX):
                lines.append(str.join("",chunk))
            dest.write(str.join("\n",lines))
            

if __name__ == '__main__':
    main()