#!/usr/bin/env  python
from __future__ import print_function

import assemble

import sys

def pivot(table):
    new_table = {}
    for key in table:
        val = table[key]
        new_table[val] = key
    return new_table

def main():
    if len(sys.argv) != 3:
        print("usage: disassemble source dest")
        exit(1)

    code_to_instr = pivot(assemble.MACHINE_CODE)
    instr_to_beef = pivot(assemble.BEEF)

    with open(sys.argv[1],'r') as source:
        with open(sys.argv[2],'w') as dest:
            tc = 0
            for line in source:
                token = line.strip()
                if token in code_to_instr:
                    dest.write(instr_to_beef[code_to_instr[token]])
                    tc = tc + 1
                else:
                    print("Invalid token: {}".format(token))
                if tc >= 80:
                    tc = 0
                    dest.write('\n')

if __name__ == "__main__":
    main()