#!/usr/bin/env python2.7
"""
Alexander Haggart, 4/14/18

Assembler for COW assembly files
    - Assembles .beef machine code from .cow assembly files
"""
import sys
import pprint as pp

NAME_TAG = '_NAME_'
PATH_TAG = '_PATH_'
TEXT_TAG = '_TEXT_'
UIDS_TAG = '_UIDS_'

IMPORT_KEYWORD = 'depends'

TEXT_KEYWORDS = {'if','else'}

class Stack(list):
    def push(self,x): #ocd
        self.append(x)
    def path(self):
        return [layer[NAME_TAG] for layer in self]

def print_usage():
    print("usage: butcher path/to/cow/file")

def parse_closures(source):
    name = []
    root = {}
    root[PATH_TAG] = ""
    root[NAME_TAG] = "/"
    root[TEXT_TAG] = []
    curr = root
    stack = Stack()
    # TODO: better parsing
    while True:
        char = source.read(1)
        if not char:
            break
        if char == '{':
            name = str.join("",name).strip()
            tmp = {}
            if name in TEXT_KEYWORDS:
                curr[TEXT_TAG].append(tmp)
            elif name in curr:
                print("Error: Namespace collision in {}.".format(stack.pop()[NAME_TAG]))
                exit(1)
            else:
                curr[name] = tmp
            tmp[NAME_TAG] = name
            tmp[TEXT_TAG] = []
            stack.push(curr)
            tmp[PATH_TAG] = stack.path() + [name]
            curr = tmp
            name = []
        else:
            if char.isspace() or char == '}':
                if name:
                    name = str.join("",name).strip()
                    curr[TEXT_TAG].append(name)
                    name = []
                if char == '}':
                    curr = stack.pop()
                    if not stack:
                        break
                continue
            name += char
    
    return root['module']

def main():
    with open(sys.argv[1]) as source:
        modules = parse_closures(source)
        pp.pprint(modules)
        module_imports = {}
        if IMPORT_KEYWORD in modules:
            module_imports.update(modules[IMPORT_KEYWORD])
     


if __name__ == '__main__':
    main()