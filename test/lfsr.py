#!/usr/bin/env python
from __future__ import print_function

import sys

def uxor(v):
    flag = False
    while v != 0:
        if v & 1:
            flag = not flag
        v = v >> 1
    return 1 if flag else 0

def lfsr_advance(seed,tap):
    return ((seed << 1) | (uxor((tap & seed)&255))) & 255

def lfsr_encrypt(seed,tap,header,message,total_len=64):
    # seed = lfsr_advance(seed,tap)
    prefix = header
    suffix = total_len - len(message) - prefix
    encrypted = []
    msg = []
    for i in range(prefix):
        msg.append(' ')
    msg.append(message)
    for i in range(suffix):
        msg.append(' ')
    message = ''.join(msg)
    print(message)
    for c in message:
        encrypted.append(seed ^ ord(c))
        seed = lfsr_advance(seed,tap)
    return encrypted

def main():
    if len(sys.argv) != 6:
        print("usage: lfsr seed tap header message dest")
        exit(1)
    seed    = int(sys.argv[1],16) # lfsr in hexadecimal
    tap     = int(sys.argv[2],16) # seed in hexadecimal
    header  = int(sys.argv[3],10) # header length in decimal
    message = sys.argv[4]
    dest = sys.argv[5]

    encrypted = lfsr_encrypt(seed,tap,header,message)
    print([hex(h) for h in encrypted])
    print(''.join([chr(v) for v in encrypted]))

    with open(dest,'wb') as file:
        for b in encrypted:
            file.write(chr(b))

if __name__ == "__main__":
    main()