#!/usr/bin/env python2.7
import sys

MACHINE_CODE = {
  "NOP" : "000000000",
  "PSH" : "110101101",	    
  "INC" : "110000000",		
  "DEC" : "110000001",		
  "MVR" : "101000010",		
  "MVL" : "101000011",
  "CBF" : "111110110",
  "CBB" : "100110111",
  "POP" : "100001101",
}

def main():
    if len(sys.argv) != 3:
        print("usage: assemble.py assembly_file machine_code_file")
    with open(sys.argv[1],"r") as assembly:
        with open(sys.argv[2],"w") as machine:
            for line in assembly:
                instr = line.strip()
                if instr in MACHINE_CODE:
                    machine.write(MACHINE_CODE[instr] + "\n")


if __name__ == "__main__":
    main()