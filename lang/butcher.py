#!/usr/bin/env python2.7
"""
Alexander Haggart, 4/14/18

Assembler for COW assembly files
    - Assembles .beef machine code from .cow assembly files
"""
import sys
import pprint as pp

def print_usage():
    print("usage: butcher path/to/cow/file")

# closure tags
NAME_TAG = '_NAME_'
PATH_TAG = '_PATH_'
TEXT_TAG = '_TEXT_'

CAPTURE_TAG = '_CAPTURE_'

# text-only tags


# namespace-only tags
BINDS_TAG = '_BINDS_'
IMPORTS_TAG = '_IMPORTS_'

# special tags
MODULE_TAG = '_MODULE_'
TREE_TAG = '_TREE_'
LEAF_TAG = '_LEAF_'

ALL_TAGS = {
    NAME_TAG,PATH_TAG,TEXT_TAG, CAPTURE_TAG,BINDS_TAG,
    IMPORTS_TAG,MODULE_TAG,LEAF_TAG,TREE_TAG
}

#keywords
PREAMBLE_KEYWORD = 'preamble'
POSTAMBLE_KEYWORD = 'postamble'
BINDINGS_KEYWORD = 'bindings'
IMPORT_KEYWORD = 'depends'

CALLING_KEYWORD = 'call'
IF_KEYWORD = 'if'
ELSE_KEYWORD = 'else'

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

TYPE_TAG = '_TYPE_'
ROOT_TYPE = 'root'
MODULE_TYPE = 'module'
NAMESPACE_TYPE = 'namespace'
PREAMBLE_TYPE = 'preamble'
POSTAMBLE_TYPE = 'postamble'
FUNCTION_TYPE = 'function'
IMPORT_TYPE = 'import'
TEXT_KEYWORD_TYPE = 'text_keyword'
BINDING_TYPE = 'binding'
BOUND_TYPE = 'bound'

def insert_function(root,leaf):
    unique = False
    print("\n\n\ngot here")
    path = leaf[PATH_TAG]
    for node in path:
        if node not in root: # insert the rest of the path
            root[node] = {}
            unique = True
        root = root[node]
    if not unique:
        print("Error: Namespace collision in {}.".format(path))
        exit(1)
    root[LEAF_TAG] = leaf

FUNCTION_FINDER = {
    TREE_TAG:lambda path:insert_function(FUNCTION_FINDER,path),
}

# type resolver helper functions
def resolve_root_child(name,parent):
    parent[MODULE_TAG] = name
    return MODULE_TYPE

def resolve_module_child(name,parent):
    if name == PREAMBLE_KEYWORD:
        return PREAMBLE_TYPE
    elif name == POSTAMBLE_KEYWORD:
        return POSTAMBLE_TYPE
    elif name == IMPORT_KEYWORD:
        return IMPORT_TYPE
    elif name == BINDINGS_KEYWORD:
        return BINDING_TYPE
    return NAMESPACE_TYPE

def resolve_binding_child(name,parent):
    return BOUND_TYPE

def resolve_namespace_child(name,parent):
    return FUNCTION_TYPE

def resolve_text_only_child(name,parent):
    if name in TEXT_KEYWORDS:
        return TEXT_KEYWORD_TYPE
    else: # should we just error out?
        print("ERROR: Closure in text-only closure: {}."
                .format(str.join("/",parent[PATH_TAG]+[name])))
        exit(1)

SORTING_HAT = {
    ROOT_TYPE:resolve_root_child,
    MODULE_TYPE:resolve_module_child,
    BINDING_TYPE:resolve_binding_child,
    NAMESPACE_TYPE:resolve_namespace_child,

    # text-only closures
    PREAMBLE_TYPE:resolve_text_only_child,
    POSTAMBLE_TYPE:resolve_text_only_child,
    FUNCTION_TYPE:resolve_text_only_child,
    TEXT_KEYWORD_TYPE:resolve_text_only_child,
    BOUND_TYPE:resolve_text_only_child,
    IMPORT_TYPE:resolve_text_only_child,
}

def process_token(name,closure):
    name = str.join("",name).strip()
    closure[TEXT_TAG].append(name)

def get_closure_type(name,parent):
    return SORTING_HAT[parent[TYPE_TAG]](name,parent)

def consume_modifiers(closure,text):
    capture_mode = 'none'
    for token in text:
        if token in PRE_BINDING_KEYWORDS:
            capture_mode = PRE_BINDING_KEYWORDS[token]
            closure[capture_mode] = []
        elif capture_mode in closure:
            closure[capture_mode].append(token)
        else:
            print("Error: Erroneous text in function signature: {}."
                    .format(closure[PATH_TAG]))
    while text: #clear the list
        text.pop()


def make_closure(parent):
    closure = {}
    if parent[TYPE_TAG] == NAMESPACE_TYPE:
        name = parent[TEXT_TAG].pop(0)
        closure[PATH_TAG] = parent[PATH_TAG] + [name]
        consume_modifiers(closure,parent[TEXT_TAG])
    else: # other types do not have modifiers
        name = parent[TEXT_TAG].pop()
        closure[PATH_TAG] = parent[PATH_TAG] + [name]
        
    closure[NAME_TAG] = name
    closure[TEXT_TAG] = []
    closure[TYPE_TAG] = get_closure_type(name,parent)
    if name in TEXT_KEYWORDS:
        parent[TEXT_TAG].append(closure)
    elif name in parent:
        print("Error: Namespace collision in {}.".format(parent[PATH_TAG]))
        exit(1)
    else:
        parent[name] = closure
        if closure[TYPE_TAG] == FUNCTION_TYPE:
            FUNCTION_FINDER[TREE_TAG](closure)
    return closure

class Stack(list):
    def push(self,x): #ocd
        self.append(x)
    def path(self):
        return [layer[NAME_TAG] for layer in self]

def parse_closures(source):
    name = []
    root = {}
    root[PATH_TAG] = []
    root[NAME_TAG] = "root"
    root[TEXT_TAG] = []
    root[TYPE_TAG] = ROOT_TYPE
    curr = root
    stack = Stack()
    # TODO: better parsing
    while True:
        char = source.read(1)
        if not char:
            break
        if char == '{':
            process_token(name,curr)
            tmp = make_closure(curr)
            stack.push(curr)
            curr = tmp
            name = []
        else:
            if char.isspace() or char == '}':
                if name:
                    process_token(name,curr)
                    name = []
                if char == '}':
                    # TODO: resolve closures as soon as they are parsed
                    # pass tags upstream (calls within if closures?) 
                    curr = stack.pop()
                    if not stack:
                        break
                continue
            name += char
    
    return root

def parse_file(file):
    # parse the file into nexted closure format
    with open(file) as source:
        root = parse_closures(source)
        module = root[root[MODULE_TAG]]
    print("Dependencies:")

    # parse and process dependencies recursively
    for dependency in module[IMPORT_KEYWORD][TEXT_TAG]:
        print(dependency)
        # parse_file(dependency)

    # resolve imported function paths
        # transplant function tree branches onto root tree

    # resolve namespace names into IDs -- do some tree reduction magic?

    # resolve function calls and nesting
        # use PATH_TAG to find target table addresses

    # resolve text tokens into code blobs
        # resolve all bound tokens in namespace
        # resolve bound function calls into absolute
        # resolve inline closures into control structures

    # resolve function calls into stack operations

    # assemble function call table

    # resolve function closures into countdown blocks

    # resolve *amble closures into code blobs
    return module

def main():
    # parse the base module
    base_module = parse_file(sys.argv[1])
    pp.pprint(base_module)
    pp.pprint(FUNCTION_FINDER)
     


if __name__ == '__main__':
    main()