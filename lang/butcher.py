#!/usr/bin/env python2.7
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
    NAME_TAG,PATH_TAG,TEXT_TAG, CAPTURE_TAG,BINDS_TAG,
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

TYPE_TAG = '_TYPE_'

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

class Tree(): # for organizing dependencies
    def __init__(self,name,data):
        self.name = name
        self.data = data
        self.children = {}
    def graft(self,branch):
        # prevent cyclic grafts
        branch = branch.prune(self.name)
        self.children[branch.name] = branch
    def prune(self,name):
        deep_copy = Tree(self.name,self.data)
        for child in self.children:
            if self.children[child].name != name:
                deep_copy.graft(self.children[child].prune(name))
        return deep_copy
    def display(self,indent=0):
        print("{}{}".format(
            str.join('',['  ' for i in range(0,indent)]),
            self.name
        ))
        for child in self.children:
            self.children[child].display(indent+1)

def upgrade_layer_entry(self,name):
    del self.contents[name]
    layer = DependencyLayer(name,self)
    return layer

def indented_print(name,indent):
    print("{}{}".format(
        str.join('',['  ' for i in range(0,indent)]),
        name
    ))

class DependencyLayer():
    def __init__(self,name,parent=None):
        self.contents = {}
        self.name = name
        if parent:
            self.trace = parent.trace + [name]
            parent.insert(self)
        else:
            self.trace = [name]
    
    # find an item in this layer's contents
    def find(self,item):
        if item in self.contents:
            return self.contents[item]
        compiler_error("Could not resolve dependency",[item])

    def insert(self,item):
        if item.name in self.contents and self.contents[item.name]:
            compiler_error("Namespace collision",item.trace)
        self.contents[item.name] = item
        return (lambda: upgrade_layer_entry(self,item.name))
    

    # compile dependencies for a set of this layer's contents
    def collect(self,items):
        # this layer's scope
        collection = {}
        print("trace: {}".format(self.trace))
        for item in items:
            item = item[:]
            print("item: {}".format(item))
            name = item.pop(0)
            path = item
            print("path: {}".format(path))
            collection[name] = self.find(name).collect([path])
        return collection

    # traverse this layer and assign future contents
    def complete(self,external):
        for item in self.contents:
            if not self.contents[item] and item in external:
                self.contents[item] = external[item]
            else:
                self.contents[item].complete(external)

    def add_future_contents(self,name):
        if name in self.contents:
            compiler_error("Namespace collision",self.trace+[item])
        self.contents[name] = None

    def print_contents(self,indent=0):
        indented_print(self.name,indent)
        for item in self.contents:
            if self.contents[item]:
                self.contents[item].print_contents(indent+1)
            else: # unfinished future items
                indented_print(item,indent+1)

class LazyDependencyNode():
    def __init__(self,name,container,trace):
        self.siblings = {}
        self.container = container 
        self.dependencies = {}
        self.trace = trace
        self.name = name
        self.upgrade_hook = self.container.insert(self) # trees con be updated into containers

    def collect(self,items=[[]]):
        if items[0]:
            compiler_error("Indexing into non-namespace",self.trace+items)
        if not self.dependencies:
            self.dependencies[self.name] = LEAF_TAG
            links = [self.siblings[sibling] for sibling in self.siblings]
            self.dependencies.update(self.container.collect(links))
        return self.dependencies

    def link(self,sibling):
        if sibling[0] != self.name:
            self.siblings[sibling[0]] = sibling

    def complete(self,external):
        pass

    def upgrade_to_layer(self):
        return self.upgrade_hook()

    def print_contents(self,indent=0):
        indented_print(self.name,indent)
        for sibling in self.siblings:
            indented_print(str.join(" ",self.siblings[sibling]),indent+1)


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
    return NAMESPACE_TYPE

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
    closure[TREE_TAG] = closure[TREE_TAG].upgrade_to_layer()

def strip_module_name(name):
    return name.split('/')[-1].split(".")[0]

def process_token(name,closure):
    name = str.join("",name).strip()
    if closure[TYPE_TAG] == IMPORT_TYPE:
        exported_trees = parse_file(name)[EXPORTS_TAG]
        external_module_name = strip_module_name(name)
        module_imports = closure[IMPORTS_TAG]
        # print(closure[PATH_TAG])
        # print(module_imports)
        module_imports[FUNCTION_EXPORT][external_module_name] = exported_trees[FUNCTION_EXPORT]
        module_imports[BINDING_EXPORT] [external_module_name] = exported_trees[BINDING_EXPORT]
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
            if capture_mode == IMPORTS_TAG:
                closure[TREE_TAG].add_future_contents(token)
        else:
            compiler_error(
                "Erroneous text in function signature",
                closure[PATH_TAG])
    while text: #clear the list
        text.pop()

def link_parent_closure(parent,child):
    parent[TREE_TAG].link(child[TEXT_TAG])

def make_closure(parent):
    closure = {}
    if parent[TYPE_TAG] == ROOT_TYPE:
        parent[MODULE_TAG] = closure
    if parent[TYPE_TAG] == NAMESPACE_TYPE:
        name = parent[TEXT_TAG].pop(0)
        closure[PATH_TAG] = parent[PATH_TAG] + [name]
        closure[TREE_TAG] = LazyDependencyNode(
                                name,
                                parent[TREE_TAG],
                                closure[PATH_TAG])
        consume_modifiers(closure,parent[TEXT_TAG])
    else: # other types do not have modifiers
        name = parent[TEXT_TAG].pop()
        closure[PATH_TAG] = parent[PATH_TAG] + [name]
        
    closure[NAME_TAG] = name
    closure[TEXT_TAG] = []
    closure[TYPE_TAG] = get_closure_type(closure,parent)

    if closure[TYPE_TAG] == NAMESPACE_TYPE and parent[TYPE_TAG] == MODULE_TYPE:
        closure[TREE_TAG] = DependencyLayer(name,parent[EXPORTS_TAG][FUNCTION_EXPORT])
    elif closure[TYPE_TAG] == PREAMBLE_TYPE: # this is temprorary
        closure[TREE_TAG] = LazyDependencyNode(name,parent[EXPORTS_TAG][FUNCTION_EXPORT],closure[PATH_TAG])

    closure[FINALIZE_TAG] = (lambda: 0) # do nothing
    
    # type-specific tags
    if closure[TYPE_TAG] == BOUND_TYPE or closure[TYPE_TAG] == FUNCTION_TYPE:
        closure[CALLS_TAG] = []
    elif closure[TYPE_TAG] == IMPORT_TYPE:
        closure[IMPORTS_TAG] = {
            FUNCTION_EXPORT:{},
            BINDING_EXPORT:{},
        }
    elif closure[TYPE_TAG] == MODULE_TYPE:
        closure[EXPORTS_TAG] = {
            FUNCTION_EXPORT: DependencyLayer(name),
            BINDING_EXPORT:  DependencyLayer(name),
        }


    # text keyword closures remain in the text section
    if name in TEXT_KEYWORDS:
        parent[TEXT_TAG].append(closure)
        if name == CALLING_KEYWORD:
            # parent[CALLS_TAG].append(closure)
            closure[FINALIZE_TAG] = lambda: link_parent_closure(parent,closure)
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

    # resolve imports into dependency tree
    if DEPENDS_KEYWORD in module:
        function_imports = module[DEPENDS_KEYWORD][IMPORTS_TAG][FUNCTION_EXPORT]
        module[EXPORTS_TAG][FUNCTION_EXPORT].complete(function_imports)
        

    # resolve bindings
        # resolve function calls within bindings
    # for binding in module[EXPORTS_TAG][BINDING_EXPORT]:
    #     graft_caller_dependencies(module,module[EXPORTS_TAG][BINDING_EXPORT][binding])
    #     module[EXPORTS_TAG][BINDING_EXPORT][binding].display()
    # resolve imported function paths
        # graft function tree branches onto root tree
    # graft_imported_modules(module)
    # expand_function_paths(module)

    # resolve function calls and nesting
        # use PATH_TAG to find target table addresses

    return module

def main():
    # parse the base module
    base_module = parse_file(sys.argv[1])
    base_module[EXPORTS_TAG][FUNCTION_EXPORT].print_contents()
    pp.pprint(base_module)

    # collect dependencies from dependency tree
    dependencies = base_module[PREAMBLE_KEYWORD][TREE_TAG].collect()
    pp.pprint(dependencies)

    # resolve namespace names into IDs -- do some tree reduction magic?

    # resolve text tokens into code blobs
        # resolve all bound tokens in namespace
        # resolve bound function calls into absolute
        # resolve inline closures into control structures

    # resolve function calls into stack operations

    # assemble function call table

    # resolve function closures into countdown blocks

    # resolve *amble closures into code blobs

def module_find_function(module,path):
    curr = module
    unfinished = None
    for node in path:
        if node == module[NAME_TAG]:
            continue
        if node in curr:
            curr = curr[node]
        else:
            unfinished = node
            break
    if unfinished: # start looking in imported modules
        # unfinished calls are due to namespace imports
        function_name = unfinished
        if curr[TYPE_TAG] != NAMESPACE_TYPE: 
            compiler_error("Malformed function call",path)
        if IMPORTS_TAG not in curr:
            compiler_error("Unable to find function for call",full_path)
        module_imports = module[DEPENDS_KEYWORD][IMPORTS_TAG]
        for external in curr[IMPORTS_TAG]: # imports are in precedence order
            if not external in module_imports:
                compiler_error("Imported module not listed as dependency",[external])

            # search in the imported module
            exported_functions = module_imports[external][EXPORTS_TAG][FUNCTION_EXPORT]
            if function_name not in exported_functions:
                continue

            # return the dependency tree for the exported function
            return exported_functions[function_name]
            # imported_function,containing_module = module_find_function(
            #     module_imports[external],
            #     [external] + [NAMESPACE_KEYWORD] + unfinished)
            # if imported_function: # found it
            #     return imported_function,containing_module
        compiler_error("Unable to find function for call",path)

    # this is the function closure that matches the path
    return curr[TREE_TAG]

def graft_caller_dependencies(module,root,shallow=False,ignore=set()):
    closure = root.data
    for call in closure[CALLS_TAG]:
        full_path = build_function_call_path(call,closure[TYPE_TAG])
        full_path_str = str.join("/",full_path)
        if full_path_str in ignore:
            return
        ignore.add(full_path_str)
        # print(call)
        target_dependencies = module_find_function(module,full_path)
        if not shallow:
            graft_caller_dependencies(containing_module,dependency,shallow,ignore)
        root.graft(dependency)

def graft_imported_modules(module):
    # for call in module[CALLS_TAG]:
    #     path = graft_path(call)
    #     deepest,remaining = attempt_path_traverse(module,path)
    #     if not remaining: # successfully found target function
    #         # do some linking stuff
    #         return 
    #     # look in the import section of the deepest context we reached
    #     if deepest[TYPE_TAG] != NAMESPACE_TYPE:
    #         compiler_error("Malformed function call path",path)
    #     if IMPORTS_TAG not in deepest:
    #         err_no_target_for_path(path)
    #     # start looking in imported modules
    #     for external in deepest[IMPORTS_TAG]:
    #         if external not in module[DEPENDS_KEYWORD][IMPORTS_TAG]:
    #             err_no_target_for_path(path)
    #         # TODO: processed modules should expose functions with EXPORTS_TAG
    #         # new_namespace = module[DEPENDS_KEYWORD][IMPORTS_TAG][external][EXPORTS_TAG]
    pass

def err_no_target_for_path(path):
    compiler_error("Unable to locate target for call",path)

def build_function_call_path(call_closure,calling_type):
    prefix = call_closure[PATH_TAG][0:-1]
    # print("before: {}".format(prefix))
    if calling_type == BOUND_TYPE:
        prefix = [prefix[0]] + [NAMESPACE_KEYWORD]
    path = prefix + call_closure[TEXT_TAG]
    # print("after: {}".format(path))
    return path

def attempt_path_traverse(module,path):
    curr = module
    unfinished = []
    for node in path:
        if not unfinished:
            if node == module[NAME_TAG]:
                continue
            if node in curr:
                curr = curr[node]
            else:
                unfinished.append(node)
        else:
            unfinished.append(node)

    return curr,unfinished


def expand_dependencies():
    pass

# traverse module structure and expand call closure text into relative function
# paths
def expand_function_paths(module):
    pass
     


if __name__ == '__main__':
    main()