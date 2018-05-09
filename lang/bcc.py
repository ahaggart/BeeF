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

# CONSTANTS ####################################################################

# VARIABLES (NONTERMINALS)
# important subtree labels
MODULE_VAR      = "module_closure"
IMPORT_VAR      = "depends_closure"
PREAMBLE_VAR    = "preamble_closure"
NAMESPACE_VAR   = "namespace_closure"
POSTAMBLE_VAR   = "postamble_closure"
BINDINGS_VAR    = "bindings_closure"

BINDING_BLOCKS_VAR  = "binding_closures"
BINDING_BLOCK_VAR   = "binding_block"
BINDING_TEXT_VAR    = "binding_text"

BOUND_KEYWORD_VAR   = "bound_keyword"

BLOCKS_VAR      = "functional_blocks"

NEST_VAR        = "nested_namespace_closure"
FUNC_VAR        = "function_closure"
TEXT_VAR        = "inline_text"

TOKEN_VAR       = "text_token"
INLINE_VAR      = "inline_closure"
SCOPE_VAR       = "scope"
BIND_VAR        = "bind"
BIND_BODY_VAR   = "bind_statement"
BIND_TEXT_VAR   = "non_empty_binding_text"
KEYWORD_VAR     = "keyword_closure"

ASSEMBLY_VAR    = "raw_assembly"
MODIFIER_VAR    = "modifier"
MODIFIER_DEC_VAR= "modifier_declaration"

KEYWORD_TERM    = "keyword"

# SCOPE METADATA
# use a tuple to prevent name collisions with other data
DEPTH_INFO      = ("DEPTH","INFO")  
KEYWORD_INFO    = ("BOUND","KEYWORDS")
MODULE_INFO     = ("MODULE","NAME")
MAPPING_INFO    = ("MAPPING","INFO")

# TAGS
# important grammar terminals and generics
NAME_TAG    = 'name'
NUMBER_TAG  = 'number'
MODULES_TAG = 'module_names'
BINDING_TAG = "binding"
LAYOUT_TAG  = "layout"

EXT = ".cow"

# TOP LEVEL COMPILER ROUTINE ###################################################

def build(module,parser,path):
    pp.pprint(module)
    # 1. Collect dependencies from tree, expanding the master scope until all
    #       dependencies are included
    loader = lambda(name):module_loader(name,parser,path)
    master_scope = build_master_scope(module,loader)

    # 2. Resolve inline text
    #       a. Resolve bindings and modifier applications
    #       b. Resolve non-call inline closures

    # use a Scope object for managing variable scope
    # object will mutate with each closure yielded by generator,
    # and will represent the variable scope of the closure
    scope = Scope()
    scope.enter() # create a top level scope for bindings
    set_block_depth(scope,0)

    # add metadata for keywords that are accessible from scope
    scope.bind(KEYWORD_INFO,set())
    scope.bind(MAPPING_INFO,dict())

    # populate the global scope with module bindings
    for binding in traverse_module_bindings(master_scope,scope):
        add_global_binding(scope,binding[BINDING_BLOCK_VAR])

    # in-order module code traversal
    for closure in traverse_module_text(master_scope,scope):
        process_inline_closure(closure,scope)
    
    scope.exit()

    # 3. Create soft links between dependent code and depended module
    # 4. Build namespace tables for each module
    # 5. Build master namespace table
    # 6. Resolve soft links into table indices
    # 7. Wrap namespace table entries in counting block structure
    # 8. Build preamble and postamble text
    return

# HIGH LEVEL HELPER FUNCTIONS ##################################################

def parse(source,parser):
    tree = parser.parse(source)
    assert(MODULE_VAR in tree)
    tree = Util.unroll(tree,parser.grammar)

    module = tree[MODULE_VAR]

    assert NAMESPACE_VAR in module,"No namespace in module: {}".format(root_module)
    assert BINDINGS_VAR in module,"No bindings in module: {}".format(root_module)

    return module

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
    errstr = "Root module name must match file name: {} in {}".format(
        mod[NAME_TAG],fname)
    assert mod[NAME_TAG] == module_name,errstr
    return mod

def collect_dependencies(module,acc,new_added):
    if IMPORT_VAR in module and module[IMPORT_VAR][MODULES_TAG] != None:
        for dep in module[IMPORT_VAR][MODULES_TAG]:
            depname = dep[NAME_TAG]
            if depname not in acc:
                acc.add(depname)
                new_added.add(depname)

def brace_splitter(regex,token):
    return [tk for tk in regex.split(token) if tk]

def make_source_reader(file):
    brace_splitter_regex= re.compile("([{}()])")
    token_fn = lambda(tk):brace_splitter(brace_splitter_regex,tk)
    return Tokenizer(SourceReader(file),token_fn)

# RECURSIVE TREE TRAVERSAL AND SCOPE MANAGMENT #################################

def traverse_module_bindings(base,scope):
    for name in base:
        module = base[name]
        bindings = module[BINDINGS_VAR][BINDING_BLOCKS_VAR]
        bind_current_module_name(scope,module[NAME_TAG])
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
        bind_current_module(scope,module)
        for text in traverse_namespace_text(module[NAMESPACE_VAR],scope):
            yield text
    scope.exit() # exit the global scope

def traverse_namespace_text(namespace,scope):
    if namespace[BLOCKS_VAR] == None:
        return
    scope.enter() # create a scope for this namespace
    increase_block_depth(scope) # used for external function call resolution
    for block in namespace[BLOCKS_VAR]:
        for text in traverse_block_text(block,scope):
            yield text
    scope.exit() # exit namespace scope

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
    scope.exit() # exit the local scope

# CLOSURE PROCESSING STUFF #####################################################

def process_inline_closure(closure,scope):
    # pp.pprint(closure)
    if TOKEN_VAR in closure:
        process_text_closure(closure[TOKEN_VAR],scope)
    elif BIND_VAR in closure:
        process_bind_closure(closure,scope)

def process_text_closure(closure,scope):
    # pp.pprint(closure)
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

def process_bind_closure(closure,scope):
    # pp.pprint(closure)
    body = closure[BIND_BODY_VAR]
    name = body[NAME_TAG]

    # module binding
    if BIND_TEXT_VAR not in body:
        if NAME_TAG not in body:
            handler.error("Malformed inline binding: {}".format(closure))
        bind_module(scope,body[NAME_TAG])
        return
    
    # inline binding: convert to the standard binding format
    text = body[BIND_TEXT_VAR].copy()

    binding_text = text.pop(BINDING_TEXT_VAR)
    if binding_text == None:
        binding_text = []
    prefix = text # get whatever else is there and prepend to list
    binding_text.insert(0,prefix)
    binding = {
        MODIFIER_DEC_VAR:None,
        BINDING_TEXT_VAR:binding_text,
        NAME_TAG:name
    }
    scope.bind(make_binding_var(binding[NAME_TAG]),binding)

    # add this keyword to the bound keywords for this scope
    bound = scope.get(KEYWORD_INFO).copy()
    bound.add(name)
    scope.bind(KEYWORD_INFO,bound)
      
def resolve_keyword(closure,scope):
    keyword = closure[BOUND_KEYWORD_VAR]
    if keyword not in scope.get(KEYWORD_INFO):
        raise KeyError("Keyword not in scope: {}".format(keyword))
    # print("FOUND MAPPING FOR {}:".format(keyword))
    # print(scope)
    # pp.pprint(scope.get(make_binding_var(keyword)))

# SCOPE MANAGEMENT HELPER FUNCTIONS ############################################

def increase_block_depth(scope):
    depth = scope.get(DEPTH_INFO)
    return scope.bind(DEPTH_INFO,depth+1)

def set_block_depth(scope,depth):
    return scope.bind(DEPTH_INFO,depth)

def get_block_depth(scope):
    return scope.get(DEPTH_INFO)

def add_global_binding(scope,binding):
    binding_name = binding[NAME_TAG]
    module_name = scope.get(MODULE_INFO)

    mapping = scope.get(MAPPING_INFO).copy()
    if module_name not in mapping:
        mapping[module_name] = set()
    mapping[module_name].add(binding_name)
    scope.bind(MAPPING_INFO,mapping)

    binding_var = make_binding_var(binding_name,module_name)
    return scope.bind(binding_var,binding)

def make_binding_var(binding,module=None):
    if module:
        return (BINDING_TAG,module,binding)
    else:
        return (BINDING_TAG,binding)

def make_layout_var(layout):
    return (LAYOUT_TAG,None)

def bind_current_module(scope,module):
    bind_current_module_name(scope,module[NAME_TAG])
    # implicitly bind the module's bindings
    bind_module(scope,module[NAME_TAG]) 

def bind_current_module_name(scope,name):
    scope.bind(MODULE_INFO,name) # bind the module name to metadata

def bind_module(scope,name):
    # print("BINDING MODULE: {}".format(name))
    bound_list = scope.get(KEYWORD_INFO).copy()
    for bname in scope.get(MAPPING_INFO)[name]:
        global_var = make_binding_var(bname,name)
        scoped_var = make_binding_var(bname)
        # print("BINDING {} to {}".format(global_var,scoped_var))

        # bind global definition into local definition
        scope.bind(scoped_var,scope.get(global_var))

        bound_list.add(bname)
    scope.bind(KEYWORD_INFO,bound_list)

# HELPER CLASSES ###############################################################

class Scope:
    def __init__(self):
        self.defined = Stack()
        self.curr_symbols = set()
        self.symbols = {}

    def __str__(self):
        return pp.pformat(self.snapshot())

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