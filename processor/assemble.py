#!/usr/bin/env python2.7
import sys

NOP = "NOP"
PSH = "PSH"
INC = "INC"
DEC = "DEC"
MVR = "MVR"
MVL = "MVL"
CBF = "CBF"
CBB = "CBB"
POP = "POP"

MACHINE_CODE = {
  NOP : "000000000",
  PSH : "110101101",	    
  INC : "110000000",		
  DEC : "110000001",		
  MVR : "101000010",		
  MVL : "101000011",
  CBF : "111110110",
  CBB : "100110111",
  POP : "100001101",
}

BEEF = {
    "[" : CBF,
    "]" : CBB,
    "+" : INC,
    "-" : DEC,
    "^" : PSH,
    "_" : POP,
    ">" : MVR,
    "<" : MVL
}

def main():
    assembly_source     = None
    machine_code_dest   = None
    if len(sys.argv) != 3:
        print("usage: assemble.py assembly_file machine_code_file")
    with open(sys.argv[1],"r") as assembly:
        with open(sys.argv[2],"w") as machine:
            for line in assembly:
                instr = line.strip()
                chars = list(instr)
                if any([c for c in chars if c in BEEF]):
                    for c in chars:
                        if c in BEEF:
                            emit(machine,MACHINE_CODE[BEEF[c]])
                elif instr in MACHINE_CODE:
                    emit(machine,MACHINE_CODE[instr])

def emit(file,text): # insert a NOP so we can see whats going on in memory
    file.write(text + '\n' + MACHINE_CODE[NOP] + '\n')


if __name__ == "__main__":
    main()