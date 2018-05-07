#!/usr/bin/env python2.7
"""
    CFG-based compiler
"""
from __future__ import print_function
import sys
import re
import json
import pprint as pp

from parse import ParsingAutomaton,Grammar,Util

MODULE_VAR      = "module_closure"
IMPORT_VAR      = "depends_closure"
PREAMBLE_VAR    = "preamble_closure"
NAMESPACE_VAR   = "namespace_closure"
POSTAMBLE_VAR   = "postamble_closure"
BINDINGS_VAR    = "bindings_closure"

# compile BeeF from a syntax tree
def compile_tree(tree,path):
    print(path)
    # pp.pprint(tree)
    assert(MODULE_VAR in tree)

    module = tree[MODULE_VAR]

    tree = Util.unroll(tree,'inline_text')
    tree = Util.unroll(tree,'functional_blocks')
    tree = Util.unroll(tree,'module_names')

    pp.pprint(tree)

    if IMPORT_VAR in module:
        print("found imports")
        for item in module[IMPORT_VAR]:
            pass

    if PREAMBLE_VAR in module:
        print("found preamble")

    if POSTAMBLE_VAR in module:
        print("found postamble")

    assert(NAMESPACE_VAR in module)
    assert(BINDINGS_VAR in module)

class Tokenizer:
    def __init__(self,source,token_fn=None):
        self.source = source
        self.pre    = []
        self.post   = []
        self.token_fn = token_fn if token_fn else lambda(x):[x]

    def __iter__(self): # pass the token lists through the filter
        for tk in self.pre:
            for _tk in self.token_fn(tk):
                yield(_tk)        
        for tk in self.source:
            for _tk in self.token_fn(tk):
                yield(_tk)
        for tk in self.post:
            for _tk in self.token_fn(tk):
                yield(_tk)
    
    def prepend(self,token):
        self.pre.insert(0,token)

    def append(self,token):
        self.post.append(token)

class SourceReader:
    def __init__(self,file):
        self.file = file
        self.line = 0
    
    def __iter__(self):
        self.line = 0
        for line in self.file:
            for token in line.strip().split():
                yield token
            self.line = self.line + 1

def brace_splitter(regex,token):
    return [tk for tk in regex.split(token) if tk]

def compile_module(source):
    with open("cow.json","r") as src:
        g = Grammar.create(json.loads(src.read()))

    parser = ParsingAutomaton("PARSER",g)

    brace_splitter_regex= re.compile("([{}()])")
    token_fn = lambda(tk):brace_splitter(brace_splitter_regex,tk)

    with open(source,"r") as f:
        tree = parser.parse(Tokenizer(SourceReader(f),token_fn))

    path = str.split(source,"/")    
    compile_tree(tree,path)

def main():
    compile_module("../code/test.cow")
        
if __name__ == '__main__':
    main()