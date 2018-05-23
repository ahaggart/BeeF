#!/usr/bin/env python2.7
import sys
from assemble import BEEF

def find_pc(program,pc):
    pos = 0
    lc = 1
    cc = 1
    while pos < pc:
        c = program.read(1)
        if c is None:
            print("Unable to find PC")
            exit(1)
        cc = cc + 1
        if c == '\n' or c == '#':
            if c == '#':
                program.readline()
            lc = lc + 1
            cc = 0
        elif c in BEEF:
            pos = pos + 1
    return lc,cc
    


def main():
    if len(sys.argv) != 3:
        print("usage: pc_finder file PC")
        exit(1)
    fname = str(sys.argv[1])
    with open(fname) as program:
        pc = int(sys.argv[2])
        lc,cc = find_pc(program,pc)
    print("PC in {} at line {} column {}".format(fname,lc,cc))
    

if __name__ == "__main__":
    main()