#!/usr/bin/env python2.7
"""
    CFG-based compiler
"""
from __future__ import print_function
import sys
import re
import json
import pprint as pp

from parse import ParsingAutomaton,Grammar,Util,Stack

MODULE_VAR      = "module_closure"
IMPORT_VAR      = "depends_closure"
PREAMBLE_VAR    = "preamble_closure"
NAMESPACE_VAR   = "namespace_closure"
POSTAMBLE_VAR   = "postamble_closure"
BINDINGS_VAR    = "bindings_closure"

BLOCKS_VAR      = "functional_blocks"

NEST_VAR        = "nested_namespace_closure"
FUNC_VAR        = "function_closure"
TEXT_VAR        = "inline_text"

TOKEN_VAR       = "text_token"
INLINE_VAR      = "inline_closure"
SCOPE_VAR       = "scope"
BIND_VAR        = "bind"
KEYWORD_VAR     = "keyword_closure"

KEYWORD_TERM    = "keyword"

NAME_TAG = 'name'
MODULES_TAG = 'module_names'

EXT = ".cow"

# compile BeeF from a syntax tree
def parse(source,parser):
    tree = parser.parse(source)
    assert(MODULE_VAR in tree)
    tree = Util.unroll(tree)

    module = tree[MODULE_VAR]

    assert NAMESPACE_VAR in module,"No namespace in module: {}".format(root_module)
    assert BINDINGS_VAR in module,"No bindings in module: {}".format(root_module)

    return module

def build(module,parser,path):
    # 1. Collect dependencies from tree, expanding the master scope until all
    #       dependencies are included
    loader = lambda(name):module_loader(name,parser,path)
    master_scope = build_master_scope(module,loader)

    # 2. Resolve inline text
    #       a. Resolve bindings and modifier applications
    #       b. Resolve non-call inline closures
    scope = Scope()
    for closure in traverse_module_text(master_scope,scope):
        pp.pprint(closure)
        pass # do a thing

    # 3. Create soft links between dependent code and depended module
    # 4. Build namespace tables for each module
    # 5. Build master namespace table
    # 6. Resolve soft links into table indices
    # 7. Wrap namespace table entries in counting block structure
    # 8. Build preamble and postamble text
    return

def build_master_scope(root_module,module_loader_fn):
    master_scope = { root_module[NAME_TAG] : root_module }
    includes = set([root_module[NAME_TAG]])
    new_modules = set()
    collect_dependencies(root_module,includes,new_modules)

    while new_modules:
        new_added = set()
        for m in new_modules:
            mod = module_loader_fn(m)
            master_scope[m] = mod
            collect_dependencies(mod,includes,new_added)
        new_modules = new_added

    return master_scope

def module_loader(module_name,parser,path):
    fname = str.join("/",path + [module_name + EXT])
    with open(fname,'r') as msrc: # find and parse the file
        mod = parse(make_source_reader(msrc),parser)
    assert mod[NAME_TAG] == module_name,"Root module name must match file name: {} in {}".format(mod[NAME_TAG],fname)
    return mod

def collect_dependencies(module,acc,new_added):
    if IMPORT_VAR in module and module[IMPORT_VAR][MODULES_TAG] != None:
        for dep in module[IMPORT_VAR][MODULES_TAG]:
            depname = dep[NAME_TAG]
            if depname not in acc:
                acc.add(depname)
                new_added.add(depname)

def traverse_module_text(base,scope):
    scope.enter() # create a global scope
    for name in base:
        module = base[name]
        for text in traverse_namespace_text(module[NAMESPACE_VAR],scope):
            yield text
    scope.exit() # exit the global scope

def traverse_namespace_text(namespace,scope):
    if namespace[BLOCKS_VAR] == None:
        return
    for block in namespace[BLOCKS_VAR]:
        for text in traverse_block_text(block,scope):
            yield text

def traverse_block_text(block,scope):
    if FUNC_VAR in block:
        for text in traverse_function_text(block[FUNC_VAR],scope):
            yield text
    elif NEST_VAR in block:
        for text in traverse_namespace_text(block[NEST_VAR],scope):
            yield text

def traverse_function_text(func,scope):
    if func[TEXT_VAR] == None:
        return
    for text in traverse_scoped_text(func[TEXT_VAR],scope):
        yield text

def traverse_scoped_text(inline,scope):
    if inline == None:
        return
    scope.enter() # create a local scope
    for text in inline:
        if TOKEN_VAR in text:
            yield text
        elif INLINE_VAR in text and KEYWORD_VAR in text[INLINE_VAR]:
            sub = text[INLINE_VAR][KEYWORD_VAR]
            if BIND_VAR in sub:
                yield sub
            elif KEYWORD_TERM in sub:
                for txt in traverse_scoped_text(sub[TEXT_VAR],scope):
                    yield txt
    scope.exit()

class Scope:
    def __init__(self):
        self.defined = Stack()
        self.curr_symbols = set()
        self.symbols = {}

    def get(self,symbol):
        if symbol not in self.symbols:
            raise KeyError("Symbol not in scope: {}".format(symbol))            
        return self.symbols[symbol].peek()

    def bind(self,symbol,value):
        if symbol in self.curr_symbols:
            self.symbols[symbol].swap(value)
        else:
            if symbol not in self.symbols:
                self.symbols[symbol] = Stack()
            self.symbols[symbol].push(value)
            self.curr_symbols.add(symbol)
    
    def enter(self):
        self.defined.push(self.curr_symbols.copy())
        self.curr_symbols = set()

    def exit(self):
        if not len(self.defined):
            raise IndexError("Exiting base scope")
        for symbol in self.curr_symbols:
            self.symbols[symbol].pop()
        self.curr_symbols = self.defined.pop()


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

def make_source_reader(file):
    brace_splitter_regex= re.compile("([{}()])")
    token_fn = lambda(tk):brace_splitter(brace_splitter_regex,tk)
    return Tokenizer(SourceReader(file),token_fn)

def compile_module(source):
    with open("cow.json","r") as src:
        g = Grammar.create(json.loads(src.read()))

    parser = ParsingAutomaton("PARSER",g)
    path = str.split(source,"/")
    root_module_name = path.pop().split(".")[0]

    module = module_loader(root_module_name,parser,path)

    build(module,parser,path)  
    

def main():
    compile_module("../code/test.cow")
        
if __name__ == '__main__':
    main()