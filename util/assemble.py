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
HLT = "HLT"

MACHINE_CODE = {
  NOP : "000000000",
  INC : "000000001",		
  DEC : "000000010",		
  MVR : "000000100",		
  MVL : "000001000",
  PSH : "000010000",	    
  POP : "000100000",
  CBF : "001000000",
  CBB : "010000000",
  HLT : "100000000"
}

BEEF = {
    "[" : CBF,
    "]" : CBB,
    "+" : INC,
    "-" : DEC,
    "^" : PSH,
    "_" : POP,
    ">" : MVR,
    "<" : MVL,
    "%" : NOP,
    "!" : HLT
}

def main():
    assembly_source     = None
    machine_code_dest   = None
    mode = "w"
    if "-a" in sys.argv:
        sys.argv.remove("-a")
        mode = "a"
    halted = False
    if len(sys.argv) != 3:
        print("usage: assemble.py assembly_file machine_code_file")
    with open(sys.argv[1],"r") as assembly:
        with open(sys.argv[2],mode) as machine:
            # buffer the assembly for startup weirdness
            for i in range(10):
                emit(machine,MACHINE_CODE[NOP])
            emit(machine,MACHINE_CODE[MVR])
            emit(machine,MACHINE_CODE[MVL])
            for line in assembly:
                halted = False
                instr = line.strip()
                chars = list(instr)
                if any([c for c in chars if c in BEEF]):
                    for c in chars:
                        halted = False
                        if c in BEEF:
                            emit(machine,MACHINE_CODE[BEEF[c]])
                            if c == "!":
                                halted = True
                elif instr in MACHINE_CODE:
                    emit(machine,MACHINE_CODE[instr])
                    if instr == HLT:
                        halted = True
            if not halted:
                emit(machine,MACHINE_CODE[HLT])

def emit(file,text): # insert a NOP so we can see whats going on in memory
    # file.write(text + '\n' + MACHINE_CODE[NOP] + '\n')
    file.write(text + '\n')


if __name__ == "__main__":
    main()