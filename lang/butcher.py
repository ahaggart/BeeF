#!/usr/bin/env python2.7
"""
Alexander Haggart, 4/14/18

Assembler for COW assembly files
    - Assembles .beef machine code from .cow assembly files
"""
from __future__ import print_function
import sys
import traceback
import pprint as pp
import re

def print_usage():
    print("usage: butcher path_to_cow_file path_to_beef_file")
    exit(1)

def compiler_error(msg,path):
    print("Error: " + msg + ": {}".format(str.join("/",path)))
    traceback.print_stack()
    exit(1)

# common tags
NAME_TAG        = '_NAME_'
PATH_TAG        = '_PATH_'
TEXT_TAG        = '_TEXT_'
TYPE_TAG        = '_TYPE_'

# namespace and binding tags
BINDS_TAG       = '_BINDS_'
IMPORTS_TAG     = '_IMPORTS_'

# special tags
MODULE_TAG      = '_MODULE_'
BUILDER_TAG     = '_BUILDER_'
CALLS_TAG       = '_CALLS_'
EXPORTS_TAG     = '_EXPORTS_'
FINALIZE_TAG    = '_FINALIZE_'

ALL_TAGS = {
    NAME_TAG,
    TYPE_TAG,
    PATH_TAG,
    TEXT_TAG,
    BINDS_TAG,
    IMPORTS_TAG,
    MODULE_TAG,
    BUILDER_TAG,
    CALLS_TAG,
    EXPORTS_TAG,
    FINALIZE_TAG
}

#keywords
PREAMBLE_KEYWORD    = 'preamble'
POSTAMBLE_KEYWORD   = 'postamble'
BINDINGS_KEYWORD    = 'bindings'
DEPENDS_KEYWORD     = 'depends'
NAMESPACE_KEYWORD   = 'namespace'

CALLING_KEYWORD     = 'call'
IF_KEYWORD          = 'if'
ELSE_KEYWORD        = 'else'

TEXT_KEYWORDS = {
    IF_KEYWORD,
    ELSE_KEYWORD,
    CALLING_KEYWORD,
}

POST_BINDING_KEYWORDS = {}

IMPORT_CAPTURE = 'imports'
BINDING_CAPTURE = 'binds'
PRE_BINDING_KEYWORDS = {
    IMPORT_CAPTURE:IMPORTS_TAG,
    BINDING_CAPTURE:BINDS_TAG
}

# closure types -- specify closure purpose, stored as a TYPE_TAG
ROOT_TYPE           = 'root'
MODULE_TYPE         = 'module'
NAMESPACE_TYPE      = 'namespace'
PREAMBLE_TYPE       = 'preamble'
POSTAMBLE_TYPE      = 'postamble'
FUNCTION_TYPE       = 'function'
IMPORT_TYPE         = 'import'
TEXT_KEYWORD_TYPE   = 'text_keyword'
BINDING_TYPE        = 'binding'
BOUND_TYPE          = 'bound'

COMMENT_DELIM = '#'

NON_ASSEMBLY_REGEX = re.compile('[^][^+><_\s#0-9-]+')
ASSEMBLY_CHARS = {'>','<','+','-','[',']','^','_'}

COUNTING_BLOCK_HEADER = "^[_-^>^[-]+^<[_[-]^]_>_<[_>"
COUNTING_BLOCK_FOOTER = "<[-]^]]_"

builtin = {
    BINDS_TAG:{
        "MVL":"<","MVR":">",
        "INC":"+","DEC":"-",
        "PUSH":"^","POP":"_",

        "ZERO":"[-]",
        "ADD":"[->+<]","SUB":"[->-<]",
        "EXIT":"<#0#>", # TODO: add an exit closure?

    }
}

# function calls create a directional dependency from the caller to the callee
# each namespace maintains a dictionary of accessible named closures
# each function maintains a set of names it is dependant upon
# calls to other functions in the same scope will merge callee set into caller set
# nested dependencies should be resolved recursively
# end goal: each namespace layer should be represented as a single subset of 
#   named closures in the namespace

# Resolving Dependencies:
#   1. Generate inter-namespace function dependency tree
#   2. Generate dependencies on nested layers, per node
#   3. Compile all depended nodes for a given set of dependencies on the layer
#       a. Pass depended list to nested layers as dependency set
#   4. Sort depended nodes by <dependencies> - <depending>
#       a. assign nodes a function id (fid) based on ordering
#   5. resolve dependency links into (namespace,fid) pairs

class Namespace():
    def __init__(self,namespace,closure_type=NAMESPACE_TYPE):
        # pass in the root module
        self.name = namespace[NAME_TAG]
        self.nodes = {}     # functions in this namespace
        self.sinks = {}     # nested namespaces visible in this scope
        self.imports = []   # imported namespaces
        self.binds = []     # imported bindings
        self.bound_keywords = {}
        if closure_type == NAMESPACE_TYPE:
            self.ingest_namespace(namespace)
        else:
            self.ingest_module(namespace)

    def ingest_module(self,module):
        for closure in module:
            if closure == BINDINGS_KEYWORD:
                self.bound_keywords.update(
                    dict([(binding,module[closure][binding][TEXT_TAG]) for binding in module[closure] if binding not in ALL_TAGS]))
            if closure in ALL_TAGS: # skip tags
                continue
            elif closure == NAMESPACE_KEYWORD:
                self.ingest_namespace(module[closure])

    def ingest_namespace(self,namespace):
        for closure in namespace:
            if closure == IMPORTS_TAG: # extract from imported modules
                self.imports = namespace[closure]
                continue
            elif closure == BINDS_TAG: # extract from imported modules
                self.binds = namespace[closure]
                continue
            elif closure in ALL_TAGS: # skip any other tags
                continue
            closure_name = namespace[closure][NAME_TAG]
            closure_type = namespace[closure][TYPE_TAG]
            if closure_type == FUNCTION_TYPE:
                self.nodes[closure_name] = DependencyNode(namespace[closure],self)
            elif closure_type == NAMESPACE_TYPE:
                self.sinks[closure_name] = Namespace(namespace[closure])

    # carry out the actual namespace importing    
    def resolve_imports(self,module_imports):
        for sink in self.sinks:
            self.sinks[sink].resolve_imports(module_imports)
        to_import = set(self.imports)
        to_import.update(set(self.binds))
        for module in to_import:
            if module not in self.sinks:
                if module not in module_imports:
                    compiler_error("Could not find module",[module])
                self.sinks[module] = module_imports[module]

    def link_dependencies(self):
        self.link_internal()
        self.link_nested()

    # resolve internal dependencies    
    def link_internal(self):
        for sink in self.sinks:
            self.sinks[sink].link_internal()
        for node in self.nodes:
            self.nodes[node].reset_net_dependents()
            self.nodes[node].initial_dep_recurse()
        for node in self.nodes:
            self.nodes[node].deep_dep_recurse(self.nodes)

    # link with nested namespaces
    def link_nested(self):
        for sink in self.sinks:
            self.sinks[sink].link_nested()
        for node in self.nodes:
            self.nodes[node].initial_nested_recurse()
    
class DependencyLayer():
    def __init__(self,namespace):
        self.name      = namespace.name
        self.namespace = namespace
        self.sublayers = {}
        self.resolved  = False
        self.linked    = False
        self.compiled  = False
        self.bound     = False

        self.id = -1

        # link the namespace dependencies
        self.namespace.link_dependencies()
        pass

    # given a resolved Namespace and a set of tokens required, compile a
    # dependency layer
    def resolve(self,entry_points):
        if not entry_points: # we dont need this layer
            return
        # merge internal token sets of entry points
        internal_token_layer = set()
        for dependency in entry_points:
            if len(dependency) != 1: # only base namespace is visible, no nesting
                compiler_error("Invalid entry point function call",dependency)
            dependency = dependency[0]
            if dependency not in self.namespace.nodes:
                compiler_error("Unable to find entry point",[dependency])
            internal_token_layer.add(dependency)
            internal_token_layer.update(self.namespace.nodes[dependency].dependencies)

        # for each imported namespace, merge dependency token sets of 
        # tokens in merged internal token set
        self.layer_deps = {}
        # print("{} token layer: {}".format(self.name,internal_token_layer))
        for sink in self.namespace.sinks:
            self.sublayers[sink] = DependencyLayer(self.namespace.sinks[sink])
            sink_deps = set()
            for token in internal_token_layer:
                if sink in self.namespace.nodes[token].nested_dependencies:
                    sink_deps.update(self.namespace.nodes[token].nested_dependencies[sink])
            self.layer_deps[sink] = sink_deps
            
        # for each imported namespace, use its finalized dependency token set
        # to compile it into a dependency layer, add it as a child of this layer
        removal_candidates = []
        for layer in self.sublayers:
            if not self.layer_deps[layer]:
                removal_candidates.append(layer)
                continue
            layer_entry_points = [[token] for token in self.layer_deps[layer]]
            # print("Entry points to {} -> {}".format(layer,layer_entry_points))
            self.sublayers[layer].resolve(layer_entry_points)

        # clean up unused sublayers
        for layer in removal_candidates:
            del self.sublayers[layer]
        

        self.resolved_token_layer = list(internal_token_layer)

        self.resolved = True        
        return

    def bind(self):
        self.resolved_bindings = {}
        for layer in self.sublayers:
            self.sublayers[layer].bind()
        for binding in self.namespace.binds:
            self.resolved_bindings.update(self.sublayers[binding].resolved_bindings)
        self.resolved_bindings.update(self.namespace.bound_keywords)
        self.bound = True
        return

    def link(self):
        if not self.resolved:
            compiler_error("Attempted to link unresolved layer",[self.name])

        # organize this dependency layer into an ordered list, using some
        # deterministic optimization critereon -> net incoming/outgoing deps
            # imported code at the bottom, since it has no dependencies on 
            # importing code
            # nested namespaces at the bottom too, for the same reason
        resolved_node_layer = [self.namespace.nodes[node] for node in self.resolved_token_layer]
        resolved_node_layer.sort(DependencyNode.sort)
        fid = 1
        for node in resolved_node_layer:
            # compute function call IDs from list order
            node.fid = fid
            fid = fid + 1
            # print("{} ID: {}".format(node.name,node.fid))

        # link local namespace function calls
        for node in resolved_node_layer:
            node.link_local(self)

        # use dependency tokens to grab refs to DependencyNode objects
        # recursively link() all sublayers
        layer_list = []
        layer_id = fid
        for layer in self.sublayers:
            self.sublayers[layer].link()
            self.sublayers[layer].id = layer_id # set after linking, so that local-scope is always -1
            for node in resolved_node_layer:
                node.link(self.sublayers[layer])
            layer_list.append(self.sublayers[layer])
            layer_id = layer_id + 1

        self.resolved_namespace_layer = resolved_node_layer + layer_list

        # for node in resolved_node_layer:
        #     print("{} links: {}".format(node.name,node.links))

        self.linked = True
        pass

    def build(self,directives,external_bindings={}):
        if not self.linked:
            compiler_error("Cannot build unlinked layer",[self.name])
        if not self.bound:
            compiler_error("Attempted to build unbound layer",[self.name])

        # insert virtual machine flags
        namespace_entry_directive = "#0#namespace: {}\n".format(self.name)
        namespace_entry_ref = "#{}#".format(len(directives))
        directives.append(namespace_entry_directive)

        # build a dictionary of token expansions
        local_bindings = {}
        local_bindings.update(external_bindings) # this has some weird ramifications
        local_bindings.update(builtin[BINDS_TAG]) # protect builtin keywords
        local_bindings.update(self.resolved_bindings) # own keywords have highest priority

        # recursively build subunits
        namespace_text = []
        for node in self.resolved_namespace_layer:
            # wrap function text in functional counting blocks
            namespace_text.append(COUNTING_BLOCK_HEADER+"\n")
            namespace_text.append(node.build(directives,local_bindings))
            namespace_text.append(COUNTING_BLOCK_FOOTER+"\n")

        # wrap namespace ID table in execution loop header and footer
        namespace_text.insert(0,"<_["+namespace_entry_ref+"\n")
        namespace_text.append("_]>\n")
        
        # concatenate functional blocks and sublayers into namespace ID table
        self.function_call_table = str.join("",namespace_text)

        self.compiled = True
        return self.function_call_table


class DependencyNode():
    def __init__(self,function,container):
        # extract core information from function closure
        self.name  = function[NAME_TAG]
        self.text  = function[TEXT_TAG][:]
        self.calls = function[CALLS_TAG][:]
        self.net_dependent = 0
        self.fid = -1
        self.container = container
        self.links = [(-1,-1)]*len(self.calls)

    def reset_net_dependents(self):
        self.net_dependent = 0

    def add_dependent(self):
        self.net_dependent = self.net_dependent + 1

    def remove_dependent(self):
        self.net_dependent = self.net_dependent - 1

    def initial_dep_recurse(self):
        self.dependencies = set()
        for i in range(len(self.calls)-1,-1,-1):
            if len(self.calls[i]) == 1: # in-scope function call
                target = self.calls[i][0]
                self.remove_dependent()
                self.dependencies.add(target)
        return

    def deep_dep_recurse(self,nodes):
        old_size = 0
        new_size = len(self.dependencies)
        while old_size < new_size:
            self.do_dep_recurse(nodes)
            old_size = new_size
            new_size = len(self.dependencies)
        return

    def do_dep_recurse(self,nodes):
        for node in self.dependencies.copy():
            new_deps =  nodes[node].dependencies - self.dependencies
            self.dependencies.update(new_deps)
            for dep in new_deps:
                nodes[dep].add_dependent()

    def initial_nested_recurse(self):
        self.nested_dependencies = {}
        for i in range(len(self.calls)-1,-1,-1):
            if len(self.calls[i]) == 2: # nested-scope function call
                # print(self.calls[i])
                target = self.calls[i]
                if not target[0] in self.nested_dependencies:
                    self.nested_dependencies[target[0]] = set()
                self.nested_dependencies[target[0]].add(target[1])
        return 

    # grab refs to nodes in this layer
    def link(self,layer):
        if layer.name == self.container.name:
            self.link_local(layer)
            return

        for i in range(0,len(self.calls)):
            call = self.calls[i]
            if call[0] == layer.name:
                self.links[i] = (layer.id,layer.namespace.nodes[call[1]].fid)
        return

    def link_local(self,layer):
        for i in range(0,len(self.calls)):
            if len(self.calls[i]) == 1:
                call = self.calls[i][0]
                self.links[i] = (layer.id,layer.namespace.nodes[call].fid)
        return
    
    def sort(self,other):
        if self.net_dependent > other.net_dependent:
            return 1
        elif other.net_dependent > self.net_dependent:
            return -1
        return 0

    def build(self,directives,local_bindings):
        #TODO: move the function-specific building elsewhere
        function_entry_directive = "#0#function: {}\n".format(self.name)
        function_entry_ref = "#{}#".format(len(directives))
        directives.append(function_entry_directive)

        # keep things divided by tokens, for now
        self.raw_text = ["\t"+function_entry_ref] 
        call_counter = 0
        call_counter = self.resolve_tokens(self.raw_text,call_counter,local_bindings)
        # TODO: optimize calls to cids accessible in the same cycle
        # TODO: make compiled code easier to read?
        return str.join("\n",self.raw_text)+"\n"

    def resolve_tokens(self,build_list,call_counter,local_bindings={}):
        for token in self.text:
            call_counter = self.recursive_build(build_list,token,call_counter,local_bindings)

    def recursive_build(self,build_list,token,call_counter,local_bindings):
        if type(token) is str:
            build_list.append(self.expand_token(token,local_bindings)) 
        else: # inline keyword
            if token[NAME_TAG] == CALLING_KEYWORD:
                link = self.links[call_counter]
                link_text = self.expand_link(link)
                build_list.append(link_text)
                call_counter = call_counter + 1
            else: #TODO: finish this section, add support for more inline keywords
                token[BUILDER_TAG].prefix()
                for tk in token[TEXT_TAG]:
                    call_counter = self.recursive_build(build_list,tk,call_counter)
                token[BUILDER_TAG].suffix()
        return call_counter

    def expand_link(self,link):
        # assume we are adjacent to control cell
        function_call = ["<[-]"] # move into control cell, zero it
        if link[0] == -1: # local scope
            cid = link[1] # get the function call id directly
            function_call.append(adjust_cell_value(0,cid))
            function_call.append("^")
        else:             # nested scope
            cid = link[0] # get the scope call id
            fid = link[1]

            # push a zero to force the nested namespace to exit when done
            function_call.append("^")

            # push the fid of the func in the namespace
            function_call.append(adjust_cell_value(0,fid))
            function_call.append("^")

            # push a value to index into the nested scope
            function_call.append(adjust_cell_value(fid,cid))
            function_call.append("^")

        function_call.append(">") # move back to starting cell
        function_call.append("call")
        return  str.join("",function_call)

    # recursively unpack any token that is not pure assembly
    # TODO: detect cyclic expansions
    def expand_token(self,token,local_bindings):
        if is_assembly(token):
            return token
        else:
            if not token in local_bindings:
                compiler_error("Unable to bind token",[self.name]+[token])
            expansion = local_bindings[token]
            return str.join("",[self.expand_token(tk,local_bindings) for tk in expansion])

def adjust_cell_value(curr_value,target_value):
    adjust_dir = "+" if target_value > curr_value else "-"
    return ((adjust_dir)*abs(target_value-curr_value))

def is_assembly(token):
    if NON_ASSEMBLY_REGEX.search(token):
        return False
    return True

def indented_print(name,indent):
    print("{}{}".format(
        str.join('',['  ' for i in range(0,indent)]),
        name
    ))

class Stack(list): # for being pedantic
    def push(self,x): #ocd
        self.append(x)
    def path(self):
        return [layer[NAME_TAG] for layer in self]

# type resolver helper functions
def resolve_root_child(name,parent):
    return MODULE_TYPE

def resolve_module_child(name,parent):
    if name == PREAMBLE_KEYWORD:
        return PREAMBLE_TYPE
    elif name == POSTAMBLE_KEYWORD:
        return POSTAMBLE_TYPE
    elif name == DEPENDS_KEYWORD:
        return IMPORT_TYPE
    elif name == BINDINGS_KEYWORD:
        return BINDING_TYPE
    elif name == NAMESPACE_KEYWORD:
        return NAMESPACE_TYPE
    compiler_error("Unrecognized module member",[name])

def resolve_binding_child(name,parent):
    return BOUND_TYPE

def resolve_namespace_child(name,parent):
    return FUNCTION_TYPE

def resolve_function_child(name,parent):
    if name in TEXT_KEYWORDS:
        return TEXT_KEYWORD_TYPE
    elif not parent[TEXT_TAG]:
        upgrade_function_to_namespace(parent)
        return FUNCTION_TYPE
    print(parent[TEXT_TAG])
    compiler_error("Closure in text-only closure",parent[PATH_TAG]+[name])

def resolve_text_only_child(name,parent):
    if name in TEXT_KEYWORDS:
        return TEXT_KEYWORD_TYPE
    else: # should we just error out?
        compiler_error("Closure in text-only closure",parent[PATH_TAG]+[name])

SORTING_HAT = {
    ROOT_TYPE:resolve_root_child,
    MODULE_TYPE:resolve_module_child,
    BINDING_TYPE:resolve_binding_child,
    NAMESPACE_TYPE:resolve_namespace_child,

    # text-only closures
    PREAMBLE_TYPE:resolve_text_only_child,
    POSTAMBLE_TYPE:resolve_text_only_child,
    FUNCTION_TYPE:resolve_function_child,
    TEXT_KEYWORD_TYPE:resolve_text_only_child,
    BOUND_TYPE:resolve_text_only_child,
    IMPORT_TYPE:resolve_text_only_child,
}

def upgrade_function_to_namespace(closure):
    closure[TYPE_TAG] = NAMESPACE_TYPE
    # closure[TREE_TAG] = closure[TREE_TAG].upgrade_to_layer()

def strip_module_name(name):
    return name.split('/')[-1].split(".")[0]

def process_token(name,closure):
    name = str.join("",name).strip()
    if closure[TYPE_TAG] == IMPORT_TYPE:
        exported_namespace = parse_file(name)[EXPORTS_TAG]
        external_module_name = strip_module_name(name)
        module_imports = closure[IMPORTS_TAG]
        # print(closure[PATH_TAG])
        # print(module_imports)
        module_imports[external_module_name] = exported_namespace
        return
    closure[TEXT_TAG].append(name)

def get_closure_type(closure,parent):
    if TYPE_TAG not in closure: # if a type is already set, dont mess with it
        return SORTING_HAT[parent[TYPE_TAG]](closure[NAME_TAG],parent)
    return closure[TYPE_TAG]

def consume_modifiers(closure,text):
    capture_mode = 'none'
    for token in text:
        if token in PRE_BINDING_KEYWORDS:
            capture_mode = PRE_BINDING_KEYWORDS[token]
            closure[capture_mode] = []
            if token == IMPORT_CAPTURE:
                upgrade_function_to_namespace(closure)
        elif capture_mode in closure:
            closure[capture_mode].insert(0,token) # prefer modules imported "later"
        else:
            compiler_error(
                "Erroneous text in function signature",
                closure[NAME_TAG])
    while text: #clear the list
        text.pop() # maybe we should be using python 3

def make_closure(parent):
    closure = {}
    if parent[TYPE_TAG] == ROOT_TYPE:
        parent[MODULE_TAG] = closure
    if parent[TYPE_TAG] == NAMESPACE_TYPE:
        name = parent[TEXT_TAG].pop(0)
        consume_modifiers(closure,parent[TEXT_TAG])
    else: # other types do not have modifiers
        name = parent[TEXT_TAG].pop()
        
    closure[NAME_TAG] = name
    closure[TEXT_TAG] = []
    closure[TYPE_TAG] = get_closure_type(closure,parent)
    closure[PATH_TAG] = parent[PATH_TAG] + [name]
    closure[FINALIZE_TAG] = (lambda: 0) # do nothing
    
    # type-specific tags
    if closure[TYPE_TAG] == FUNCTION_TYPE or closure[TYPE_TAG] == PREAMBLE_TYPE:
        closure[CALLS_TAG] = []
    elif closure[TYPE_TAG] == IMPORT_TYPE:
        closure[IMPORTS_TAG] = {}
    elif closure[TYPE_TAG] == MODULE_TYPE:
        closure[EXPORTS_TAG] = None


    # text keyword closures remain in the text section
    if name in TEXT_KEYWORDS:
        parent[TEXT_TAG].append(closure)
        closure[CALLS_TAG] = parent[CALLS_TAG]
        if name == CALLING_KEYWORD:
            parent[CALLS_TAG].append(closure[TEXT_TAG])
            # closure[FINALIZE_TAG] = (lambda: print(parent[CALLS_TAG]))
    elif name in parent:
        compiler_error("Namespace collision",parent[PATH_TAG])
    else:
        parent[name] = closure            
    return closure

def parse_closures(source):
    name = []
    root = { # set up a root "closure" to build from
        PATH_TAG: [],
        NAME_TAG: "root",
        TEXT_TAG: [],
        TYPE_TAG: ROOT_TYPE,
    }
    curr = root
    stack = Stack()
    # TODO: better parsing
    while True:
        char = source.read(1)
        if not char:
            break
        if char == '{':
            if name:
                process_token(name,curr)
            tmp = make_closure(curr)
            stack.push(curr)
            curr = tmp
            name = []
        elif char == '(': #TODO: only allow this in text closures 
            digit = source.read(1)
            num = []
            while digit != ')':
                num.append(digit)
                digit = source.read(1)
            for i in range(0,int(str.join("",num))):
                process_token(name,curr)
            name = []
        else:
            # if char.isspace() or char == '}' or char == COMMENT_DELIM or char in ASSEMBLY_CHARS:
            if char.isspace() or char == '}' or char == COMMENT_DELIM:
                if name:
                    process_token(name,curr)
                    name = []
                if char == '}':
                    curr[FINALIZE_TAG]() # run a function to set up closure
                    curr = stack.pop()
                    if not stack:
                        break
                elif char == COMMENT_DELIM:
                    source.readline() # skip the rest of the line
                # elif char in ASSEMBLY_CHARS:
                #     process_token(char,curr)
                continue
            name += char
    
    return root

def parse_file(file):
    # parse the file into nexted closure format
    with open(file,"r") as source:
        module = parse_closures(source)[MODULE_TAG]

    base_namespace = Namespace(module,closure_type=MODULE_TYPE)
    if DEPENDS_KEYWORD in module:
        base_namespace.resolve_imports(module[DEPENDS_KEYWORD][IMPORTS_TAG])
    module[EXPORTS_TAG] = base_namespace

    return module

def main():
    # TODO: command-line options, etc
    if len(sys.argv) < 3:
        print_usage()

    # parse the base module
    base_module = parse_file(sys.argv[1])
    # pp.pprint(base_module)
    base_layer = DependencyLayer(base_module[EXPORTS_TAG])

    # collect dependencies from dependency tree
    base_layer.resolve(base_module[PREAMBLE_KEYWORD][CALLS_TAG])

    # traverse the tree and link it to the function objects
    base_layer.link()

    # recursize binding import
    base_layer.bind()

    # resolve text tokens into code blobs
        # resolve all bound tokens in namespace
        # resolve bound function calls into absolute
        # resolve inline closures into control structures
    directives = ["#-1#global exit condition\n"]
    # directives = []
    code = base_layer.build(directives)

    # resolve *amble closures into code blobs  
    preamble = DependencyNode(base_module[PREAMBLE_KEYWORD],None)
    preamble.link_local(base_layer)
    preamble_code = ["[-]^>"]
    preamble.resolve_tokens(preamble_code,0)
    preamble_code = str.join("",preamble_code)

    # print(preamble_code)

    with open(sys.argv[2],"w") as outfile:
        for directive in directives:
            outfile.write(directive)
        outfile.write(preamble_code)
        outfile.write(code)

if __name__ == '__main__':
    main()