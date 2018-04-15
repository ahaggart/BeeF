#!/usr/bin/env python2
"""
Alexander Haggart, 4/14/18

Assembler for COW assembly files
    - Assembles .beef machine code from .cow assembly files
"""
import sys

NAME_TAG = '_NAME_'

def stack_push(self,x):
    self.append(x)

def print_usage():
    print("usage: butcher path/to/cow/file")

def parse_closures(source):
    name = []
    module = {}
    curr = module
    stack = []
    stack.push = stack_push #ocd
    while True:
        char = source.read(1)
        if char == '{':
            closure_name = str.join(name,"").strip()
            tmp = {}
            tmp[NAME_TAG] = closure_name
            if closure_name in curr:
                print("Error: Namespace collision in {}.".format(stack.pop()[NAME_TAG]))
                exit(1)
            curr[] = tmp
            stack.push(curr)
            curr = tmp
        elif char == '}':
            curr = stack.pop()
        else:
            name += char
    
    return module

def main():
    modules = parse_modules(sys.argv[1])
    print(modules)
    pass

if __name__ == '__main__':
    main()