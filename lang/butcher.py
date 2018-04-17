#!/usr/bin/env python2.7
from __future__ import print_function

"""
Alexander Haggart, 4/14/18

Assembler for COW assembly files
    - Assembles .beef machine code from .cow assembly files

syntax:
module_name{
    preamble{

    }
    depends{

    }
    namespace{
        function_name binds other_module{
            bindings_and_raw_assembly
            if{
                
            }
            else{
            
            }
            call{
                path to function
            }
        }
        nested_namespace_name imports other_module_1 binds other_module_2{
            inner_function_name{

            }
        }
    }
    bindings{
        bound_token binds other_module{

        }
    }
    postamble{

    }
}

parse:
{
    NAME_TAG:name
    TYPE_TAG:module
}
"""
import sys
import traceback
import pprint as pp

def print_usage():
    print("usage: butcher path/to/cow/file")

# common tags
NAME_TAG        = '_NAME_'
PATH_TAG        = '_PATH_'
TEXT_TAG        = '_TEXT_'
TYPE_TAG = '_TYPE_'

# namespace and binding tags
CAPTURE_TAG     = '_CAPTURE_'
BINDS_TAG       = '_BINDS_'

# namespace-only tags
IMPORTS_TAG     = '_IMPORTS_'

# special tags
MODULE_TAG      = '_MODULE_'
TREE_TAG        = '_TREE_'
LEAF_TAG        = '_LEAF_'
BUILDER_TAG     = '_BUILDER_'

CALLS_TAG       = '_CALLS_'
ADD_CALL_TAG    = '_ADD_CALL_'

EXPORTS_TAG     = '_EXPORTS_'
ADD_EXPORT_TAG  = '_ADD_EXPORT_'
FUNCTION_EXPORT = '_FUNCTION_'
BINDING_EXPORT  = '_BINDING_'

FINALIZE_TAG = '_FINALIZE_'

ALL_TAGS = {
    NAME_TAG,PATH_TAG,TEXT_TAG, CAPTURE_TAG,BINDS_TAG,TYPE_TAG,
    IMPORTS_TAG,MODULE_TAG,LEAF_TAG,TREE_TAG,BUILDER_TAG,
    CALLS_TAG,ADD_CALL_TAG,EXPORTS_TAG,ADD_EXPORT_TAG,
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
    # CALLING_CAPTURE:CALLS_TAG,
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

#TODO: use disjoint sets for dependency handling
# function calls create a directional dependency from the caller to the callee
# each namespace maintains a dictionary of accessible named closures
# each function maintains a set of names it is dependant upon
# calls to other functions in the same scope will merge callee set into caller set
# nested dependencies should be resolved recursively
# end goal: each namespace layer should be represented as a single subset of 
#   named closures in the namespace
#   

# Resolving Dependencies:
#   1. Generate inter-namespace function dependency tree

# module[EXPORTS_TAG] = {
#   FUNCTION_EXPORT: {
#       NAME_TAG:namespace
#       function_1: {<dependencies>}
#       function_2: {<dependencies>}
#       nested_namespace: {
#           NAME_TAG: nested_namespace
#       }
#   }
#   BINDING_EXPORT:  {
# 
#   }
# }

class Namespace():
    def __init__(self,namespace,closure_type=NAMESPACE_TYPE):
        # pass in the root module
        self.name = namespace[NAME_TAG]
        self.nodes = {}     # functions in this namespace
        self.sinks = {}     # nested namespaces visible in this scope
        self.imports = []   # imported namespaces
        self.binds = []     # imported bindings
        if closure_type == NAMESPACE_TYPE:
            self.ingest_namespace(namespace)
        else:
            self.ingest_module(namespace)

    def ingest_module(self,module):
        for closure in module:
            if closure == BINDINGS_KEYWORD: # extract from imported modules
                self.binds = [module[closure][binding] for binding in module[closure] if binding not in ALL_TAGS]
            elif closure in ALL_TAGS: # skip any other tags
                continue
            elif closure == NAMESPACE_KEYWORD:
                self.ingest_namespace(module[closure])
                return

    def ingest_namespace(self,namespace):
        for closure in namespace:
            if closure == IMPORTS_TAG: # extract from imported modules
                self.imports = namespace[closure]
                continue
            elif closure == BINDS_TAG: # extract from imported modules
                self.binds   = namespace[closure]
                continue
            elif closure in ALL_TAGS: # skip any other tags
                continue
            closure_name = namespace[closure][NAME_TAG]
            closure_type = namespace[closure][TYPE_TAG]
            if closure_type == FUNCTION_TYPE:
                self.nodes[closure_name] = DependencyNode(namespace[closure])
            elif closure_type == NAMESPACE_TYPE:
                self.sinks[closure_name] = Namespace(namespace[closure])

    # carry out the actual namespace importing    
    def resolve_imports(self,module_imports):
        for sink in self.sinks:
            self.sinks[sink].resolve_imports(module_imports)
        for module in self.imports:
            if module not in self.sinks:
                self.sinks[module] = module_imports[module]

    # resolve internal dependencies    
    def link_internal(self):
        for sink in self.sinks:
            self.sinks[sink].link_internal()
        for node in self.nodes:
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
        self.linked    = False
        self.compiled  = False
        pass

    # given a resolved Namespace and a set of tokens required, compile a
    # dependency layer
    def resolve(self,entry_points):
        # merge internal token sets of entry points
        internal_token_layer = set()
        for dependency in entry_points:
            if len(dependency) != 1: # only base namespace is visible, no nesting
                compiler_error("Invalid preamble function call",dependency)
            internal_token_layer.update(self.namespace.nodes[dependency[0]].dependencies)

        # for each imported namespace, merge dependency token sets of 
        # tokens in merged internal token set
        # self.namespace.link_nested()
        for sink in self.namespace.sinks:
            self.sublayers[sink] = DependencyLayer(self.namespace.sinks[sink])

        # for each imported namespace, use its finalized dependency token set
        # to compile it into a dependency layer, add it as a child of this layer

            # self.sublayers[sink].resolve()
        pass
    
    def link(self):
        # recursively link() all sublayers

        # organize this dependency layer into an ordered list, using some
        # deterministic optimization critereon
            # imported code at the bottom, since it has no dependencies on 
            # importing code
            # nested namespaces at the bottom too, for the same reason

        # compute function call IDs from ordered list and sublayer maps

        # expand function calls into FCID stack operations
        pass

    def build(self):
        # recursively build sublayers

        # expand function text bindings into assembly

        # insert virtual machine flags?

        # wrap function text in functional counting blocks

        # concatenate functional blocks and sublayers into namespace ID table

        # wrap namespace ID table in execution loop header and footer
        pass


class DependencyNode():
    def __init__(self,function):
        # extract core information from function closure
        self.name  = function[NAME_TAG]
        self.text  = function[TEXT_TAG]
        self.calls = function[CALLS_TAG]

    def initial_dep_recurse(self):
        self.dependencies = set()
        for i in range(len(self.calls)-1,-1,-1):
            if len(self.calls[i]) == 1: # in-scope function call
                target = self.calls.pop(i)[0]
                self.dependencies.add(target)

    def deep_dep_recurse(self,nodes):
        old_size = 0
        new_size = len(self.dependencies)
        while old_size < new_size:
            self.do_dep_recurse(nodes)
            old_size = new_size
            new_size = len(self.dependencies)
        pp.pprint(self.dependencies)


    def do_dep_recurse(self,nodes):
        for node in self.dependencies.copy():
            self.dependencies.update(nodes[node].dependencies)

    def initial_nested_recurse(self):
        self.nested_dependencies = {}
        for i in range(len(self.calls)-1,-1,-1):
            if len(self.calls[i]) == 2: # nested-scope function call
                target = self.calls.pop(i)
                if not target[0] in self.nested_dependencies:
                    self.nested_dependencies[target[0]] = set()
                self.nested_dependencies[target[0]].add(target[1])
        pp.pprint(self.nested_dependencies)

class DependencyLink():
    def __init__(self,name):
        pass

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

def compiler_error(msg,path):
    print("Error: " + msg + ": {}".format(str.join("/",path)))
    traceback.print_stack()
    exit(1)

def insert_function_call(root,leaf):
    unique = False
    path = leaf[PATH_TAG]
    for node in path:
        if node not in root: # insert the rest of the path
            root[node] = {}
            unique = True
        root = root[node]
    if not unique:
        compiler_error("Namespace collision",path)
    root[LEAF_TAG] = leaf[TEXT_TAG]

FUNCTION_FINDER = {
    BUILDER_TAG:lambda path:insert_function_call(FUNCTION_FINDER,path),
}

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
    if TYPE_TAG not in closure:
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
            # if capture_mode == IMPORTS_TAG:
            #     closure[TREE_TAG].add_future_contents(token)
        else:
            compiler_error(
                "Erroneous text in function signature",
                closure[PATH_TAG])
    while text: #clear the list
        text.pop()

# def link_parent_closure(parent,child):
#     parent[TREE_TAG].link(child[TEXT_TAG])

def make_closure(parent):
    closure = {}
    if parent[TYPE_TAG] == ROOT_TYPE:
        parent[MODULE_TAG] = closure
    if parent[TYPE_TAG] == NAMESPACE_TYPE:
        name = parent[TEXT_TAG].pop(0)
        closure[PATH_TAG] = parent[PATH_TAG] + [name]
        consume_modifiers(closure,parent[TEXT_TAG])
    else: # other types do not have modifiers
        name = parent[TEXT_TAG].pop()
        closure[PATH_TAG] = parent[PATH_TAG] + [name]
        
    closure[NAME_TAG] = name
    closure[TEXT_TAG] = []
    closure[TYPE_TAG] = get_closure_type(closure,parent)
    closure[FINALIZE_TAG] = (lambda: 0) # do nothing
    
    # type-specific tags
    if closure[TYPE_TAG] == BOUND_TYPE or closure[TYPE_TAG] == FUNCTION_TYPE or closure[TYPE_TAG] == PREAMBLE_TYPE:
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
        else:
            if char.isspace() or char == '}' or char == COMMENT_DELIM:
                if name:
                    process_token(name,curr)
                    name = []
                if char == '}':
                    curr[FINALIZE_TAG]()
                    curr = stack.pop()
                    if not stack:
                        break
                elif char == COMMENT_DELIM:
                    source.readline() # skip the rest of the line
                continue
            name += char
    
    return root

# def import_namespace(tree,name):

def parse_file(file):
    # parse the file into nexted closure format
    with open(file) as source:
        module = parse_closures(source)[MODULE_TAG]

    base_namespace = Namespace(module,closure_type=MODULE_TYPE)
    if DEPENDS_KEYWORD in module:
        base_namespace.resolve_imports(module[DEPENDS_KEYWORD][IMPORTS_TAG])
    # base_namespace.link_internal()

    module[EXPORTS_TAG] = base_namespace

    return module

def main():
    # parse the base module
    base_module = parse_file(sys.argv[1])
    # base_module[EXPORTS_TAG][FUNCTION_EXPORT].print_contents()
    pp.pprint(base_module)
    base_module[EXPORTS_TAG].link_internal()
    base_module[EXPORTS_TAG].link_nested()
    base_layer = DependencyLayer(base_module[EXPORTS_TAG])

    base_layer.resolve(base_module[PREAMBLE_KEYWORD][CALLS_TAG])


    # collect dependencies from dependency tree

    # traverse the tree and link it to the function objects

    # resolve namespace names into IDs -- do some tree reduction magic?

    # resolve text tokens into code blobs
        # resolve all bound tokens in namespace
        # resolve bound function calls into absolute
        # resolve inline closures into control structures

    # resolve function calls into stack operations

    # assemble function call table

    # resolve function closures into countdown blocks

    # resolve *amble closures into code blobs  

if __name__ == '__main__':
    main()