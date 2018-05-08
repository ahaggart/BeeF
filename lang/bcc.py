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

BINDING_BLOCKS_VAR  = "binding_closures"
BINDING_BLOCK_VAR   = "binding_block"

BOUND_KEYWORD_VAR   = "bound_keyword"

BLOCKS_VAR      = "functional_blocks"

NEST_VAR        = "nested_namespace_closure"
FUNC_VAR        = "function_closure"
TEXT_VAR        = "inline_text"

TOKEN_VAR       = "text_token"
INLINE_VAR      = "inline_closure"
SCOPE_VAR       = "scope"
BIND_VAR        = "bind"
KEYWORD_VAR     = "keyword_closure"

ASSEMBLY_VAR    = "raw_assembly"
MODIFIER_VAR    = "modifier"

KEYWORD_TERM    = "keyword"

# scope metadata
# use a tuple to prevent name collisions with other data
DEPTH_INFO      = ("DEPTH","INFO")  
KEYWORD_INFO    = ("BOUND","KEYWORDS")
MODULE_INFO     = ("MODULE","NAME")

NAME_TAG = 'name'
NUMBER_TAG  =   'number'
MODULES_TAG = 'module_names'
BINDING_TAG = "binding"
LAYOUT_TAG  = "layout"

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
    scope.enter() # create a top level scope for bindings
    set_block_depth(scope,0)

    # add metadata for keywords that are accessible from scope
    scope.bind(KEYWORD_INFO,set())

    # populate the global scope with module bindings
    for binding in traverse_module_bindings(master_scope,scope):
        add_global_binding(scope,binding[BINDING_BLOCK_VAR])

    for closure in traverse_module_text(master_scope,scope):
        process_inline_closure(closure,scope)
    
    print(scope)
    scope.exit()

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

def traverse_module_bindings(base,scope):
    for name in base:
        module = base[name]
        bindings = module[BINDINGS_VAR][BINDING_BLOCKS_VAR]
        for text in traverse_binding_text(bindings,scope):
            yield text

def traverse_binding_text(base,scope):
    if base == None:
        return
    for binding in base:
        yield binding

def traverse_module_text(base,scope):
    scope.enter() # create a global scope
    for name in base:
        module = base[name]
        bind_module(scope,module)
        for text in traverse_namespace_text(module[NAMESPACE_VAR],scope):
            yield text
    scope.exit() # exit the global scope

def traverse_namespace_text(namespace,scope):
    scope.enter()
    increase_block_depth(scope)        
    if namespace[BLOCKS_VAR] == None:
        return
    for block in namespace[BLOCKS_VAR]:
        for text in traverse_block_text(block,scope):
            yield text
    scope.exit()

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
    increase_block_depth(scope)
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

def process_inline_closure(closure,scope):
    # pp.pprint(closure)
    if TOKEN_VAR in closure:
        process_text_closure(closure[TOKEN_VAR],scope)

def process_text_closure(closure,scope):
    pp.pprint(closure)
    if ASSEMBLY_VAR in closure: # raw assembly, only need to resolve modifier
        modifier = closure[MODIFIER_VAR]
        if modifier != None:
            if NAME_TAG in modifier:
                handler.error("Non-numeric modifier: {}".format(
                    modifier[NAME_TAG]))
            mod_val = int(modifier[NUMBER_TAG])
            closure[MODIFIER_VAR] = None # destroy the modifier
            # duplicate the token
            closure[ASSEMBLY_VAR] = closure[ASSEMBLY_VAR] * mod_val
    elif BOUND_KEYWORD_VAR in closure: # resolve the keyword
        # resolve the keyword into assembly and swap the tags
        closure[ASSEMBLY_VAR] = resolve_keyword(closure,scope)
        closure[MODIFIER_VAR] = None
        
def resolve_keyword(closure,scope):
    keyword = closure[BOUND_KEYWORD_VAR]
    if keyword not in scope.get(KEYWORD_INFO):
        raise KeyError("Keyword not in scope: {}".format(keyword))

def increase_block_depth(scope):
    depth = scope.get(DEPTH_INFO)
    return scope.bind(DEPTH_INFO,depth+1)

def set_block_depth(scope,depth):
    return scope.bind(DEPTH_INFO,depth)

def get_block_depth(scope):
    return scope.get(DEPTH_INFO)

def add_global_binding(scope,binding):
    return scope.bind(make_binding_var(binding),binding)

def make_binding_var(binding):
    return (BINDING_TAG,binding[NAME_TAG])

def make_layout_var(layout):
    return (LAYOUT_TAG,None)

def bind_module(scope,module):
    scope.bind(MODULE_INFO,module[NAME_TAG]) # bind the module name to metadata

    # implicitly bind the module's bindings
    curr_bindings = scope.get(KEYWORD_INFO).copy()
    for binding in module[BINDINGS_VAR][BINDING_BLOCKS_VAR]:
        curr_bindings.add(binding[BINDING_BLOCK_VAR][NAME_TAG])
    scope.bind(KEYWORD_INFO,curr_bindings)

class Scope:
    def __init__(self):
        self.defined = Stack()
        self.curr_symbols = set()
        self.symbols = {}

    def __str__(self):
        return str(self.snapshot())

    def snapshot(self):
        values = {}
        for symbol in self.symbols:
            if len(self.symbols[symbol]):
                values[symbol] = self.symbols[symbol].peek()
        return values
                

    def get(self,symbol):
        if symbol not in self.symbols or not len(self.symbols[symbol]):
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
        return value
    
    def enter(self):
        self.defined.push(self.curr_symbols.copy())
        self.curr_symbols = set()

    def exit(self):
        if not len(self.defined):
            raise IndexError("Exiting base scope")
        for symbol in self.curr_symbols:
            self.symbols[symbol].pop()
        self.curr_symbols = self.defined.pop()

class BCCErrorHandler:
    def error(self,msg):
        print("ERROR: {}".format(msg))
        exit(1)

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
    
handler = BCCErrorHandler()

def main():
    compile_module("../code/test.cow")
        
if __name__ == '__main__':
    main()