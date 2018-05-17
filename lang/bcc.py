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

KEYWORD_VAR     = "keyword_closure"

BIND_BODY_VAR   = "bind_statement"
BIND_TEXT_VAR   = "non_empty_binding_text"

LAYOUT_INNER_VAR= "layout_statement"

SET_INNER_VAR   = "set_statement"
SET_PAIR_VAR    = "set_pair"
DATA_SOURCE_VAR = "data_source"
DATA_TARGET_VAR = "data_target"
DATA_ADDRESS_VAR= "data_address"

VALUE_INNER_VAR = "value_statement"

GOTO_INNER_VAR  = "goto_statement"

ASSERT_INNER_VAR = "assert_statement"

MODIFIER_CHAIN_VAR = "modifier_chain"
MODIFIER_LIST_VAR  = "modifier_list"
MODIFIER_ARG_VAR   = "modifier_arg"

ASSEMBLY_VAR    = "raw_assembly"
MODIFIER_VAR    = "modifier"
MODIFIER_DEC_VAR= "modifier_declaration"

CALLING_VAR    = "call_closure"
CALL_PATH_VAR  = "call_path"

KEYWORD_TERM    = "keyword"

# SCOPE METADATA
# use a tuple to prevent name collisions with other data
DEPTH_INFO      = ("DEPTH","INFO")  
KEYWORD_INFO    = ("BOUND","KEYWORDS")
MODULE_INFO     = ("MODULE","NAME")
MAPPING_INFO    = ("MAPPING","INFO")
PATH_INFO       = ("PATH","INFO")
ORDER_INFO      = ("ORDER","INFO")
TRACKING_INFO   = ("TRACKING","INFO")
KNOWN_VALUE_INFO= ("KNOWN_VALUES")

TEXT_TARGET     = ("TEXT","TARGET")
REF_TABLE       = ("REF","TABLE")
FUNC_TABLE      = ("FUNCTION","TABLE")

SCOPE_CACHE     = ("SCOPE","CACHE")

TREE_DATA       = "$" # use illegal chars to avoid collisions
DEP_COUNTER     = "#"
PATH_DATA       = "%"

PREAMBLE_DATA   = "$PREAMBLE$"
POSTAMBLE_DATA  = "$POSTAMBLE$"

# TAGS
# important grammar terminals and generics
NAME_TAG    = 'name'
NUMBER_TAG  = 'number'
MODULES_TAG = 'module_names'
BINDING_TAG = "binding"
LAYOUT_TAG  = "layout"
BIND_TAG    = "bind"
SET_TAG     = "set"
SCOPE_TAG   = "scope"
REBASE_TAG  = "rebase"
LOCK_TAG    = "lock"
ASSERT_TAG  = "assert"
TEXT_TAG    = "text"
ASSEMBLY_TAG= ASSEMBLY_VAR

GOTO_TAG    = "goto"
PUSH_TAG    = "push"
POP_TAG     = "pop"
CREATE_TAG  = "create"

VALUE_TAG = "value"

ADDRESS_TAG = "address"
CONSTANT_TAG= "constant"

DATA_TAG    = "data"

PUSH_INSTR  = "^"
POP_INSTR   = "_"
RIGHT_INSTR = ">"
LEFT_INSTR  = "<"
CBF_INSTR   = "["
ABR_INSTR   = "]"
INC_INSTR   = "+"
DEC_INSTR   = "-"

ZERO_BINDING = "[-]"

COUNTING_BLOCK_HEADER = "^[_-^>^[-]+^<[_[-]^]_>_<[_>"
COUNTING_BLOCK_FOOTER = "<[-]^]]_"

EXEC_LOOP_HEADER = "<_["
EXEC_LOOP_FOOTER = "_]>"

CELL_MAX = 255

TOKEN_CHAR_REGEX = "([{},()])"

COMMENT_DELIM = "#"

EXT = ".cow"

# BUILTIN BINDINGS
BUILTINS = {
    "ADD":"[->+<]",
    "SUB":"[->-<]",
    "ZERO":"[-]",
    "PUSH":"^",
    "POP":"_",
}

# TOP LEVEL COMPILER ROUTINE ###################################################

def build(module,parser,path):
    # pp.pprint(module)
    # 1. Collect dependencies from tree, expanding the master scope until all
    #       dependencies are included
    loader = lambda(name):module_loader(name,parser,path)
    master_scope = build_master_scope(module,loader)

    # use a table to hold intermediate compiled results
    # should only contain assembly and function call prototypes
    text_table = {}

    # use a table to hold staged function calls
    call_table = []

    # when a scope exits, update the text table
    target_grabber= lambda image: update_text_table(text_table,image)

    # use a Scope object for managing variable scope
    # object will mutate with each closure yielded by generator,
    # and will represent the variable scope of the closure
    
    scope = Scope(image_hook=target_grabber)
    scope.enter() # create a top level scope for bindings
    set_block_depth(scope,0)

    # add metadata bindings for processing
    scope.bind(KEYWORD_INFO,set())
    scope.bind(MAPPING_INFO,dict())
    scope.bind(TEXT_TARGET,CopyList())
    scope.bind(PATH_INFO,CopyList())
    scope.bind(TRACKING_INFO,Stack([make_pos_tracker()]))
    scope.bind(KNOWN_VALUE_INFO,{})
    scope.bind(REF_TABLE,call_table)
    scope.bind(SCOPE_CACHE,{})

    bind_builtin_keywords(scope)

    # populate the global scope with module bindings
    for binding in traverse_module_bindings(master_scope,scope):
        add_global_binding(scope,binding[BINDING_BLOCK_VAR])

    # 2. Resolve inline text
    #       a. Resolve bindings and modifier applications
    #       b. build a text table for code structuring
    #       c. wrap functions in counting block structure

    # in-order module code traversal
    for closure in traverse_module_text(master_scope,scope):
        process_inline_closure(closure,scope)

    build_preamble(module,scope)
    build_postamble(module,scope)

    # pp.pprint(text_table)

    # 3. Create soft links between dependent code and depended module
    #       a. register function calls with a path to the calling text

    # iterate over the ref table
    # check that refs point to valid functions
    # build a dependency "graph" for table optimization
    dep_table = build_dependency_table(text_table,scope)

    # 4. Build namespace tables for each module
    #       a. collect all referenced functions
    #       b. order functions which share a scope
    # 5. Build master namespace table

    preamble_path = [module[NAME_TAG],PREAMBLE_DATA]
    depended = collect_function_dependencies(preamble_path,dep_table)

    # pp.pprint(depended)

    # 6. Resolve soft links into table indices
    path_table,base_table,order_table = resolve_table_ordering(depended,dep_table)

    cache = scope.get(SCOPE_CACHE)
    for call_info in build_call_stacks(depended,path_table):
        call_stack = call_info[0]
        call_loc   = call_info[1]
        insert_function_call(text_table,call_stack,call_loc,cache)

    # print("PATHS:")
    # pp.pprint(path_table)


    # build functions into base table
    master_table =build_master_table(text_table,base_table,depended,order_table)

    # pp.pprint(master_table)

    # 8. Wrap namespace table entries in counting block structure
    exec_loop = wrap_and_flatten_text(master_table)

    # pp.pprint(exec_loop)

    # 9. Build preamble and postamble text
    master_text = build_from_table_path(text_table,preamble_path)
    master_text.extend(exec_loop)

    postamble_path = [module[NAME_TAG],POSTAMBLE_DATA]
    postamble_text = build_from_table_path(text_table,postamble_path)
    master_text.extend(postamble_text)
    
    scope.exit()

    return master_text

# HIGH LEVEL HELPER FUNCTIONS ##################################################

def parse(source,parser):
    tree = parser.parse(source)
    assert(MODULE_VAR in tree)
    tree = Util.unroll(tree,parser.grammar)

    module = tree[MODULE_VAR]

    assert NAMESPACE_VAR in module,"No namespace in module: {}".format(module[NAME_TAG])
    assert BINDINGS_VAR in module,"No bindings in module: {}".format(module[NAME_TAG])

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
    if IMPORT_VAR in module and module[IMPORT_VAR][MODULES_TAG] is not None:
        for dep in module[IMPORT_VAR][MODULES_TAG]:
            depname = dep[NAME_TAG]
            if depname not in acc:
                acc.add(depname)
                new_added.add(depname)

def brace_splitter(regex,token):
    return [tk for tk in regex.split(token) if tk]

def make_source_reader(file):
    brace_splitter_regex= re.compile(TOKEN_CHAR_REGEX)
    token_fn = lambda(tk):brace_splitter(brace_splitter_regex,tk)
    return Tokenizer(SourceReader(file),token_fn)

def update_text_table(table,image):
    table_insert(table,image[PATH_INFO],image[TEXT_TARGET])

def table_insert(table,path,data):
    leaf = table_index(table,path)
    if leaf is None:
        return
    leaf[TREE_DATA] = data

def table_insert_list(table,path,data):
    leaf = table_index(table,path)
    if leaf is None:
        return
    if TREE_DATA not in leaf:
        leaf[TREE_DATA] = []
    leaf[TREE_DATA].append(data)

def table_get(table,path,default=None):
    leaf = table_index(table,path)
    if TREE_DATA not in leaf:
        return default
    return leaf[TREE_DATA]

def table_transform(table,path,func,default):
    leaf = table_index(table,path)
    if TREE_DATA not in leaf:
        data = default
    else:
        data = leaf[TREE_DATA]
    leaf[TREE_DATA] = func(data)

def table_index(table,path):
    curr = table
    path = path[:]
    if not path:
        return # fail quietly
    while path:
        i = path.pop(0)
        if i not in curr:
            curr[i] = {}
        curr = curr[i]
    return curr

def table_check(table,path):
    path = path[:]
    if not path:
        return False
    while path:
        table = table.get(path.pop(0),None)
        if not table:
            return False
    return True

def extract_path(path):
    path = path[:]
    while path:
        node = path.pop()
        try: # loop until we hit a non-numeric entry
            int(node)
        except:
            break
    return path,node

def build_dependency_table(text_table,scope):
    dep_table = {}
    inc_score = lambda s: s+1
    dec_score = lambda s: s-1

    for ref in scope.get(REF_TABLE):
        local_scope,func_name = extract_path(ref[0])
        call_path = ref[1][:]
        first = call_path.pop(0)
        path_error = KeyError("Could not find function for path: {}".format(ref[1]))
        local_path = local_scope+[first]
        full_path = local_scope+[func_name]
        if table_check(text_table,local_path): # local scope
            if call_path:
                local_path = local_path+call_path
                if not table_check(text_table,local_path):
                    raise path_error
            else:
                # track net reference direction (incoming/outgoing) for table
                # order optimization 
                table_transform(dep_table,make_score_path(full_path),dec_score,0)
                table_transform(dep_table,make_score_path(local_path),inc_score,0)

            table_insert_list(dep_table,full_path,local_path)

        elif call_path and first in text_table: # global scope
            inner = call_path.pop()
            if inner not in text_table[first]:
                raise path_error
            table_insert_list(dep_table,full_path,ref[1])
        else:
            raise path_error
        
        # insert the path to the function call in the text table
        # this will allow us to directly inject function call text later
        table_insert_list(dep_table,make_path_path(full_path),ref[0])
    return dep_table

def build_call_table(dep_table): # build function call table from dep table
    pass

def make_score_path(path):
    return path + [DEP_COUNTER]

def make_path_path(path):
    return path + [PATH_DATA]

def build_from_table_path(table,path):
    for node in path:
        name = node
        enc_table = table
        table = table[node]
    return build_from_table(enc_table,name)

def build_from_table(table,entry,target=None):
    if target is None:
        target = []
    text = table[entry][TREE_DATA]
    for token in text:
        if token in table[entry]:
            build_from_table(table[entry],token,target)
        else:
            target.append(token)
    return target

def build_preamble(module,scope):
    # create a fake environment to evaluate the preamble in
    with scope.inner() as scope:
        # set things up as if we were in the base namespace
        bind_current_module(scope,module)  
        with scope.use(PATH_INFO) as path:
            path.append(module[NAME_TAG])
            path.append(PREAMBLE_DATA)

        scope.bind(ORDER_INFO,0)   
        preamble = module[PREAMBLE_VAR]
        for inline in traverse_unscoped_text(preamble[TEXT_VAR],scope):
            process_inline_closure(inline,scope)

def build_postamble(module,scope):
    # create a fake environment to evaluate the preamble in
    with scope.inner() as scope:
        # set things up as if we were in the base namespace
        bind_current_module(scope,module)  
        with scope.use(PATH_INFO) as path:
            path.append(module[NAME_TAG])
            path.append(POSTAMBLE_DATA)

        scope.bind(ORDER_INFO,0)
        scope.bind(TRACKING_INFO,Stack([make_pos_tracker(0)]))
        postamble = module[POSTAMBLE_VAR]
        process_binding_text(pack_binding_text(postamble),scope)

def collect_function_dependencies(entry,table,acc=None):
    if acc is None:
        acc = dict()
    leaf = table_index(table,entry)
    if TREE_DATA not in leaf:
        return
    for i in range(0,len(leaf[TREE_DATA])):
        dep = leaf[TREE_DATA][i]
        full_path = leaf[PATH_DATA][TREE_DATA][i]
        dep_tuple = tuple(dep)
        if dep_tuple not in acc:
            acc[dep_tuple] = []
            collect_function_dependencies(dep,table,acc)
        acc[dep_tuple].append(full_path)
    return acc

def resolve_table_ordering(dep_map,dep_table):
    # resolve path fragments in to table indices
    fragment_map = {}
    for path in dep_map:
        fragment = []
        for node in path:
            if not fragment:
                fragment.append(node)
                continue
            frag_key = tuple(fragment)
            fragment.append(node)
            if frag_key not in fragment_map:
                fragment_map[frag_key] = []
            score = table_get(dep_table,make_score_path(fragment),None)
            ascending_insert(fragment_map[frag_key],node,score)

    len_cmp = lambda a,b:len(a)-len(b)
    sorted_fragment_keys = sorted(list(fragment_map.keys()),len_cmp)

    fragment_order = {}
    module_count = 0
    base_table = []
    for frag in sorted_fragment_keys:
        if len(frag) == 1 and frag not in fragment_order:
            fragment_order[frag] = len(base_table)
            base_table.append([])
        curr_table = base_table
        path = []
        for i in range(0,len(frag)):
            path.append(frag[i])
            curr_table = curr_table[fragment_order[tuple(path)]]
        
        for item in fragment_map[frag]:
            full_path = tuple(path+[item[0]])
            if full_path not in fragment_order:
                fragment_order[full_path] = len(curr_table)
                curr_table.append([])

    path_table = {}
    for path in dep_map:
        curr_table = base_table
        frag = []
        call_path = []
        for node in path:
            frag.append(node)
            idx = fragment_order[tuple(frag)]
            call_path.append(idx)
            curr_table = curr_table[idx]
        
        path_table[path] = call_path
        # curr_table.append('x')

    return path_table,base_table,fragment_order

def ascending_insert(table,item,score):
    if score is None:
        table.append((item,None))
        return len(table) - 1

    for i in range(0,len(table)):
        if table[i][1] is None or score < table[i][1]:
            table.insert(i,(item,score))
            return i

    table.append((item,score))
    return len(table) - 1

def make_local_stack(path,block,path_table):
    call_path = []
    resolved_path = path_table[block]
    for i in range(0,len(resolved_path)):
        call_path.append(resolved_path[i]+1)
    path = tuple(path)
    if path in path_table:
        return_path = path_table[path]
        for i in range(0,len(return_path)-1):
            call_path.append(return_path[i]+1)
    return call_path

def make_exit_stack(path,block,path_table):
    exit_stack = [0]*(len(path)-1)
    return exit_stack + make_local_stack(path,block,path_table)

def build_call_stacks(depended,path_table):
    for block in depended:
        depending = depended[block]
        for dep in depending:
            dep_path,node = extract_path(dep)
            if node != PREAMBLE_DATA:
                dep_path.append(node)
            else:
                dep_path = [node]
            call_stack = [0]*(len(dep_path)-1)
            call_stack.extend(make_local_stack(dep_path,block,path_table))
            call_stack.reverse()
            # resolve the call stack to assembly and inject it
            # remove the leading zero from preamble call
            yield (call_stack,dep)

def insert_function_call(text_table,call_stack,call_path,cache):
    # build a scope from the cached image
    scope = Scope(image=cache[tuple(call_path)])

    # if call_path[1] == PREAMBLE_DATA: # pop the scope return from preamble call
    #     call_stack.pop()

    text = compile_call_stack(call_stack,scope)
    target = cache[tuple(call_path)][TEXT_TARGET] # direct ref to the text table
    target.append("$$$")
    target.extend(text)
    target.append("$$$")

def compile_call_stack(stack,scope):
    # cached scope allows us to use goto, create, and assembly closures
    # to build in-scope optimized call routines using assertions
    addr = get_tracked_pos(scope)
    # print("calling @ addr: {}".format(addr))
    actions = []
    actions.append(make_goto_closure(addr-1))
    for value in stack:
        actions.append(make_create_closure(addr-1,value))
        actions.append(make_assembly_closure(PUSH_INSTR))
    actions.append(make_goto_closure(addr))

    for action in actions:
        process_inline_closure(action,scope)

    return scope.get(TEXT_TARGET)

def build_master_table(text_table,base_table,depending,order_table):
    def order_fn(path):
        return order_table[path]
    def order_cmp(a,b):
        return order_fn(b) - order_fn(a)

    resolve_list = sorted(depending.keys(),order_cmp)

    for fn in resolve_list:
        fragment = []
        curr_table = base_table
        for node in fn:
            fragment.append(node)
            fkey = tuple(fragment)
            curr_table = curr_table[order_table[fkey]]
        curr_table.append(fn[-1])
        curr_table.extend(build_from_table_path(text_table,fn))
    
    return base_table

def wrap_and_flatten_text(master_table,dest=None):
    if dest is None:
        dest = []
    func        = False
    namespace   = False
    dest.append(EXEC_LOOP_HEADER)
    for item in master_table:
        if item.__class__.__name__ ==  "list":
            assert not func
            if not namespace:
                namespace = True
            dest.append(COUNTING_BLOCK_HEADER)
            wrap_and_flatten_text(item,dest)
            dest.append(COUNTING_BLOCK_FOOTER)            
        else:
            assert not namespace
            if not func:
                dest.pop()
                func = True
            dest.append(item)
    assert namespace ^ func
    if namespace:
        dest.append(EXEC_LOOP_FOOTER)
    return dest


# RECURSIVE TREE TRAVERSAL AND SCOPE MANAGMENT #################################

def traverse_module_bindings(base,scope):
    for name in base:
        module = base[name]
        bindings = module[BINDINGS_VAR][BINDING_BLOCKS_VAR]
        bind_current_module_name(scope,module[NAME_TAG])
        for text in traverse_binding_text(bindings,scope):
            yield text

def traverse_binding_text(base,scope):
    if base is None:
        return
    for binding in base:
        yield binding

def traverse_module_text(base,scope):
    with scope.inner() as scope:
        for name in base:
            module = base[name]
            bind_current_module(scope,module)
            for text in traverse_namespace_text(module[NAMESPACE_VAR],scope):
                yield text

def traverse_namespace_text(namespace,scope):
    if namespace[BLOCKS_VAR] is None:
        return

    with scope.inner() as scope:
        increase_block_depth(scope) # used for external function call resolution

        # update the path for this scope
        if NAME_TAG in namespace:
            append_path(scope,namespace[NAME_TAG])
        else:
            append_path(scope,scope.get(MODULE_INFO))
        
        # emit_raw_text(EXEC_LOOP_HEADER,scope)
        for block in namespace[BLOCKS_VAR]:
            for text in traverse_block_text(block,scope):
                yield text
        # emit_raw_text(EXEC_LOOP_FOOTER,scope)


def traverse_block_text(block,scope):
    if FUNC_VAR in block:
        for text in traverse_function_text(block[FUNC_VAR],scope):
            yield text
    elif NEST_VAR in block:
        for text in traverse_namespace_text(block[NEST_VAR],scope):
            yield text

def traverse_function_text(func,scope):    
    # create an itermediate scope for path resolution
    with scope.inner() as scope:
        append_path(scope,func[NAME_TAG])
        update_tracking(scope,0) # create a tracking scope
        # emit_tracked_text(COUNTING_BLOCK_HEADER,scope)
        # update_tracking(scope,0) # rebase to 0 on function entry
        
        if func[TEXT_VAR] is not None:
            for text in traverse_scoped_text(func[TEXT_VAR],scope):
                yield text
        # emit_tracked_text(COUNTING_BLOCK_FOOTER,scope)


def traverse_scoped_text(inline,scope):
    if inline is None:
        return
    order = update_scope_order(scope)

    with scope.inner() as scope:
        append_path(scope,order)
        for text in traverse_unscoped_text(inline,scope):
            yield text

def traverse_unscoped_text(inline,scope):
    # pp.pprint(inline)
    if inline is None:
        return
    for text in inline:
        if TOKEN_VAR in text:
            yield text
        else:
            if KEYWORD_VAR in text[INLINE_VAR]:
                sub = text[INLINE_VAR][KEYWORD_VAR]
                if SCOPE_TAG in sub:
                    for txt in traverse_scoped_text(sub[TEXT_VAR],scope):
                        yield txt
                elif LOCK_TAG in sub:
                    # maintain tracking
                    # locks do not create a new variable scope
                    # >> allow locks on bindings while still updating scope
                    # TODO: add VM locks to enforce
                    pos = get_tracked_pos(scope)
                    for txt in traverse_unscoped_text(sub[TEXT_VAR],scope):
                        yield txt
                    update_tracking(scope,pos)
                else:
                    yield sub
            else: # call closure
                call = text[INLINE_VAR][CALLING_VAR]
                yield call

# CLOSURE PROCESSING STUFF #####################################################

def process_inline_closure(closure,scope):
    # pp.pprint(closure)
    if TOKEN_VAR in closure:
        process_text_closure(closure[TOKEN_VAR],scope)
    elif BIND_TAG in closure:
        process_bind_closure(closure,scope)
    elif LAYOUT_TAG in closure:
        process_layout_closure(closure,scope)
    elif SET_TAG in closure:
        process_set_closure(closure,scope)
    elif REBASE_TAG in closure:
        process_rebase_closure(closure,scope)
    elif GOTO_TAG in closure:
        process_goto_closure(closure,scope)
    elif CREATE_TAG in closure:
        process_create_closure(closure,scope)
    elif ASSERT_TAG in closure:
        process_assert_closure(closure,scope)
    elif VALUE_TAG in closure:
        process_value_closure(closure,scope)
    else: # call closure
        process_call_closure(closure,scope)

def process_text_closure(closure,scope):
    # pp.pprint(closure)
    if ASSEMBLY_VAR in closure: # raw assembly, only need to resolve modifier
        modifier = closure[MODIFIER_VAR]
        assembly = closure[ASSEMBLY_VAR]
        if modifier is not None:
            if NAME_TAG in modifier:
                vvar = make_value_var(modifier[NAME_TAG])
                if not scope.has(vvar):
                    handler.error("Non-numeric modifier: {}".format(
                        modifier))
                mod_val = scope.get(vvar)
            elif ASSEMBLY_TAG in modifier:
                handler.error("Non-numeric modifier: {}".format(
                    modifier))
            else:
                mod_val = int(modifier[NUMBER_TAG])
            assembly = closure[ASSEMBLY_VAR] * mod_val
        emit_tracked_text(assembly,scope)
    else: # resolve the keyword
        # resolve the keyword into assembly and swap the tags
        process_bound_keyword(closure,scope)

def emit_raw_text(text,scope):
    if not text:
        return
    with scope.use(TEXT_TARGET) as target:
        target.append(text)

def emit_tracked_text(text,scope):
    if not text:
        return
    emit_raw_text(text,scope)
    tracker = get_pos_tracker(scope)
    for char in text:
        if tracker[ADDRESS_TAG] is None:
            break
        if char == RIGHT_INSTR:
            tracker[ADDRESS_TAG] = tracker[ADDRESS_TAG] + 1
        elif char == LEFT_INSTR:
            tracker[ADDRESS_TAG] = tracker[ADDRESS_TAG] - 1
        elif char == CBF_INSTR:
            track_loop_entry(scope)
        elif char == ABR_INSTR:
            track_loop_exit(scope)
        tracker = get_pos_tracker(scope)

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
    
    # inline binding    
    text = body[BIND_TEXT_VAR].copy()

    binding_text = text.pop(BINDING_TEXT_VAR)
    if binding_text is None:
        binding_text = []
    prefix = text # get whatever else is there and prepend to list
    if TOKEN_VAR in prefix:
        prefix = {TOKEN_VAR:prefix[TOKEN_VAR]}
    else:
        prefix = pack_keyword_closure({KEYWORD_VAR:prefix[KEYWORD_VAR]})
    binding_text.insert(0,prefix)

    bind_raw_text(name,binding_text,scope)

def process_layout_closure(layout,scope):
    for entry in layout[LAYOUT_INNER_VAR]:
        bind_layout_info(scope,entry)

def process_rebase_closure(closure,scope):
    base = int(closure[NUMBER_TAG])
    update_tracking(scope,base)

def process_goto_closure(closure,scope):
    curr_loc = get_tracked_pos(scope)
    if curr_loc is None:
        errstr = "Unable to resolve data head position for: {}".format(closure)
        raise ValueError(errstr)
    
    inner = closure[GOTO_INNER_VAR]
    if NAME_TAG in inner:
        dest_loc = scope.get(make_layout_var(inner[NAME_TAG]))
    else:
        dest_loc = int(inner[NUMBER_TAG])
    
    adj = RIGHT_INSTR if curr_loc < dest_loc else LEFT_INSTR
    text = adj * abs(curr_loc - dest_loc)
    emit_tracked_text(text,scope)

def process_set_closure(closure,scope):
    statement_block = []
    start_address = get_tracked_pos(scope)
    for item in closure[SET_INNER_VAR]:
        statement_block.append(process_set_statement(item[SET_PAIR_VAR],scope))
    # reorder set statements and convert to GOTO and PUSH/POP actions
    optimized = optimize_statement_block(statement_block,scope)
    optimized.append(make_goto_closure(start_address))

    for block in optimized:
        process_inline_closure(block,scope)

def process_set_statement(pair,scope):
    source = pair[DATA_SOURCE_VAR]
    target = pair[DATA_TARGET_VAR]

    if NAME_TAG in target: # resolve the target address from scope layout
        t_address = scope.get(make_layout_var(target[NAME_TAG]))
    else: # target is already an address
        t_address = int(target[DATA_ADDRESS_VAR][NUMBER_TAG])

    s_address = None
    s_type = ADDRESS_TAG
    if NAME_TAG in source: # resolve the source address from scope layout
        source_layout = make_layout_var(source[NAME_TAG])
        if scope.has(source_layout):
            s_address = scope.get(source_layout)
        else:
            s_address = int(scope.get(make_value_var(source[NAME_TAG])))
            s_type = CONSTANT_TAG
    elif DATA_ADDRESS_VAR in source: # source is an address
        s_address = int(source[DATA_ADDRESS_VAR][NUMBER_TAG])
    
    if s_address is None: # couldnt match source to a resolved type -> numeric
        s_address = int(source[NUMBER_TAG])
        s_type = CONSTANT_TAG

    return (t_address,s_address,s_type)

# optimize a group of statements for minimal code size/cycle count
def optimize_statement_block(block,scope):
    # minimize data head movement by grabbing and dropping values efficiently
    # probably need some graph theory stuff here
    # edges point from dependent node to depended node
    # have:
    # - set of nodes that must be visited
    # - set of order dependencies that must be obeyed

    # doing things stupidly for now
    pair_compare = lambda x,y:(x[0]-y[0])
    block = sorted(block[:],cmp=pair_compare)
    sources     = [pair[0] for pair in block if pair[2] == ADDRESS_TAG]

    actions = []

    for addr in sources:
        actions.append((GOTO_TAG,addr))
        actions.append((PUSH_TAG,addr))

    block.reverse()
    for triple in block:
        actions.append((GOTO_TAG,triple[0]))
        if triple[2] == ADDRESS_TAG:
            actions.append((POP_TAG, triple[1]))    # pop the grabbed value
        else:
            # create the source constant
            actions.append((CREATE_TAG, triple[0],triple[1])) 
    
    return expand_action_tags(actions,scope)

def expand_action_tags(actions,scope):
    expanded = []
    for action in actions:
        if action[0] == GOTO_TAG:
            expanded.append(make_goto_closure(action[1]))
        elif action[0] == PUSH_TAG:
            expanded.append(make_assembly_closure(PUSH_INSTR))
        elif action[0] == POP_TAG:
            expanded.append(make_assembly_closure(POP_INSTR))
        elif action[0] == CREATE_TAG:
            expanded.append(make_create_closure(action[1],action[2]))
    return expanded

class DataNode:
    def __init__(self,loc):
        self.edges = []
        self.loc = loc
    
    def add(self,node):
        self.edges.append((node,abs(self.loc-node.loc)))

# set the current location to a value
# if nearby values are known, will optimize movement and value adjustment
def process_create_closure(closure,scope):

    # worst case: no assertions
    # zero the current cell and increment/decrement it to desired value
    # big-O cost: 255 + 127 = 372
    # -> if a value is asserted somewhere, fetch it
    # --> PUSH-POP costs 2, round trip => 185-cell search space
    # -> inexact matches can be adjusted, add to cost
    WORST_CASE_CREATE = 370
    curr_addr = get_tracked_pos(scope)
    addr = int(closure[DATA_ADDRESS_VAR][NUMBER_TAG])
    target = int(closure[NUMBER_TAG])
    # print("creating value: {} @ {}".format(target,addr))

    cost_fn = lambda pair: compute_value_cost(  curr_addr,
                                                addr,
                                                target,
                                                pair[0],
                                                pair[1])

    cost_cmp = lambda a,b: cost_fn(a) - cost_fn(b)

    known_values = scope.get(KNOWN_VALUE_INFO).items()
    best = sorted(known_values,cmp=cost_cmp,reverse=True)
    if best:
        best = best.pop()
    else:
        best = (curr_addr+1000,0) # make some garbage that will get rejected

    if cost_fn(best) > WORST_CASE_CREATE:
        actions = [
            make_goto_closure(addr),
            make_assembly_closure(ZERO_BINDING),
            make_adjustment_text(0,target,INC_INSTR,DEC_INSTR,CELL_MAX)
        ]
    else:
        # print("using value @ {}".format(best[0]))
        actions = [
            make_goto_closure(best[0]),
            make_assembly_closure(PUSH_INSTR),
            make_goto_closure(addr),
            make_assembly_closure(POP_INSTR),
            make_adjustment_text(best[1],target,INC_INSTR,DEC_INSTR,CELL_MAX)
        ]
    actions.append(make_assert_closure(addr,target))
    actions.append(make_goto_closure(curr_addr))
    for action in actions:
        process_inline_closure(action,scope)

def compute_value_cost(curr_addr,base_addr,target_value,source_addr,source_value):
    to_cost = abs(curr_addr - source_addr)
    from_cost = abs(base_addr - source_addr)
    adj_cost = abs(target_value - source_value)
    return  to_cost + from_cost + adj_cost

def process_assert_closure(closure,scope):
    if VALUE_TAG in closure[ASSERT_INNER_VAR]:
        process_value_assertion(closure,scope)

def process_value_assertion(closure,scope):
    # TODO: add VM assertions to enforce this
    statement = closure[ASSERT_INNER_VAR]
    addr = int(statement[DATA_ADDRESS_VAR][NUMBER_TAG])
    val = int(statement[NUMBER_TAG])
    with scope.use(KNOWN_VALUE_INFO) as kv:
        kv[addr] = val
   
def process_bound_keyword(closure,scope): # resolve a bound keyword into assembly
    # pp.pprint(closure)
    keyword = closure[BOUND_KEYWORD_VAR]
    if keyword not in scope.get(KEYWORD_INFO):
        raise KeyError("Keyword not in scope: {}".format(keyword))
    
    # grab the binding from the local scope
    binding = scope.get(make_binding_var(keyword))

    # build a partial scope for resolving modifiers
    partial = {}

    # this is a bad way to do this
    # TODO: add a way to intercept emitted text and duplicate it
    dups = 1

    if closure[MODIFIER_VAR] is not None:
        # print("got here {}".format(keyword))
        modifiers = closure[MODIFIER_VAR]
        binding_def = format_binding_def(binding)
        apperr = "Cannot apply {} to binding: {}".format(
                format_modifiers(modifiers),binding_def)
        matcherr = "Cannot match \"{}\" to \"{}\" in {}"
        if binding[MODIFIER_DEC_VAR] is not None:
            applied = build_modifier_chain(modifiers)
            declared = binding[MODIFIER_DEC_VAR][MODIFIER_LIST_VAR]

            if len(applied) != len(declared):
                raise ValueError(apperr)

            mods = [dec[MODIFIER_ARG_VAR][NAME_TAG] for dec in declared]

            for i in range(0,len(declared)):
                param = declared[i][MODIFIER_ARG_VAR]
                arg = applied[i]
                arg_val = arg[1]
                match_error = ValueError(matcherr.format(arg_val,param[NAME_TAG],binding_def))

                if LAYOUT_TAG in param:
                    layout_var = make_layout_var(arg_val)
                    local_var  = make_layout_var(param[NAME_TAG]) 
                    if not scope.has(layout_var):
                        raise match_error
                    partial[local_var] = scope.get(layout_var)
                elif VALUE_TAG in param: # expecting a number
                    if arg[0] == NUMBER_TAG: # raw number
                        partial[make_value_var(param[NAME_TAG])] = int(arg[1])
                    elif arg[0] == NAME_TAG: # named number (param forwarding)
                        vvar = make_value_var(arg[NAME_TAG])
                        pvar = make_value_var(param[NAME_TAG])
                        partial[pvar] = scope.get(vvar)
                    else:
                        raise match_error
                elif TEXT_TAG in param: # expecting a keyword or raw assembly
                    kvar = make_binding_var(param[NAME_TAG])
                    # build a fake binding to implement text substitution
                    if arg[0] == NAME_TAG:
                        bvar = make_bound_keyword_closure(arg[1])
                    elif arg[0] == ASSEMBLY_TAG:
                        bvar = make_assembly_closure(arg[1])
                    else:
                        raise match_error
                    partial[kvar] = pack_into_binding_text(param[NAME_TAG],[bvar])
                    if KEYWORD_INFO not in partial:
                        partial[KEYWORD_INFO] = scope.get(KEYWORD_INFO).copy()
                    partial[KEYWORD_INFO].add(param[NAME_TAG])
                else:
                    raise ValueError(apperr)
        else: # binding does not declare any modifiers, treat as raw text
            if NUMBER_TAG in modifiers:
                dups = int(modifiers[NUMBER_TAG])
            elif NAME_TAG in modifiers:
                vvar = make_value_var(modifiers[NAME_TAG])
                if not scope.has(vvar):
                    raise ValueError(apperr)
                dups = scope.get(vvar)
            elif modifiers[MODIFIER_CHAIN_VAR] is not None:
                raise ValueError(apperr)
            pass
    elif binding[MODIFIER_DEC_VAR] is not None:
        # binding expects modifiers
        raise ValueError("Binding {} expects modifiers".format(keyword))

    with scope.partial(partial) as scope:
        count = 0
        while count < dups:
            process_binding_text(binding,scope)
            count = count + 1

def process_binding_text(closure,scope):
    # recursively resolve text in this binding
    for text in traverse_unscoped_text(closure[BINDING_TEXT_VAR],scope):
        process_inline_closure(text,scope)

def process_value_closure(closure,scope):
    for statement in closure[VALUE_INNER_VAR]:
        scope.bind(make_value_var(statement[NAME_TAG]),statement[NUMBER_TAG])

def process_call_closure(call,scope):
    errstr = "expected a call closure, got: {}".format(call)
    assert CALL_PATH_VAR in call, errstr
    path = call[CALL_PATH_VAR][NAME_TAG]
    
    # insert a placeholder for the function call
    # add the call and path to the global list
    order = update_scope_order(scope)
    with scope.inner() as scope:
        append_path(scope,order)
        path_list = path if path.__class__.__name__ == "list" else [path]
        scope.get(REF_TABLE).append((scope.get(PATH_INFO),path_list))
        snapshot = scope.snapshot()
        snapshot[TRACKING_INFO] = Stack([make_pos_tracker(get_tracked_pos(scope))])
        scope.get(SCOPE_CACHE)[tuple(scope.get(PATH_INFO))] = snapshot

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

    with scope.use(MAPPING_INFO) as mapping:
        if module_name not in mapping:
            mapping[module_name] = set()
        mapping[module_name].add(binding_name)

    binding_var = make_binding_var(binding_name,module_name)
    return scope.bind(binding_var,pack_binding_text(binding))

def pack_binding_text(binding):
    # pack binding text as if it were normal inline text
    # we can reuse processing functions on binding text this way
    if binding[BINDING_TEXT_VAR] is None:
        return binding
    packed = []
    for closure in binding[BINDING_TEXT_VAR]:
        if KEYWORD_VAR in closure:
            packed.append(pack_inline_closure(closure))
        else:
            packed.append(closure)
    binding[BINDING_TEXT_VAR] = packed
    return binding

def pack_inline_closure(closure):
    return { INLINE_VAR: closure }

def pack_into_binding_text(name,text):
    return { 
        BINDING_TEXT_VAR:text,
        NAME_TAG:name,
        MODIFIER_DEC_VAR:None,
    }

def append_path(scope,name):
    with scope.use(PATH_INFO) as path:
        path.append(name)

    # clear this scope's text target
    scope.bind(TEXT_TARGET,CopyList())
    scope.bind(ORDER_INFO,0)

def update_scope_order(scope):
    order = scope.get(ORDER_INFO)
    with scope.use(TEXT_TARGET) as target:
        target.append(order)
    scope.bind(ORDER_INFO,order+1)
    return order

def make_pos_tracker(addr=None):
    return { ADDRESS_TAG:addr }

def get_pos_tracker(scope):
    return scope.get(TRACKING_INFO).peek()

def update_tracking(scope,addr):
    # print("Setting tracking to: {}".format(addr))
    get_pos_tracker(scope)[ADDRESS_TAG] = addr

def get_tracked_pos(scope):
    pos = get_pos_tracker(scope)
    return pos[ADDRESS_TAG]

def invalidate_tracking(scope):
    update_tracking(scope,None)

def create_tracking_scope(scope):
    tracker = scope.get(TRACKING_INFO)
    tracker.push(tracker.peek().copy())

def destroy_tracking_scope(scope):
    return scope.get(TRACKING_INFO).pop()

def track_loop_entry(scope):
    create_tracking_scope(scope)

def track_loop_exit(scope): # pop the current tracking scope
    old = destroy_tracking_scope(scope)

    # if tracking is invalid, nullify enclosing tracking
    if old[ADDRESS_TAG] is None:
        invalidate_tracking(scope)

def make_binding_var(binding,module=None):
    if module:
        return (BINDING_TAG,module,binding)
    else:
        return (BINDING_TAG,binding)

def make_layout_var(layout):
    return (LAYOUT_TAG,layout)

def make_value_var(name):
    return (VALUE_TAG,name)

def make_goto_closure(addr):
    return {
        GOTO_TAG:GOTO_TAG,
        GOTO_INNER_VAR:{
            NUMBER_TAG:addr,
        }
    }

def make_assembly_closure(text):
    return {
        TOKEN_VAR:{
            MODIFIER_VAR:None,
            ASSEMBLY_VAR:text,
        }
    }

def make_bound_keyword_closure(keyword):
    return {
        TOKEN_VAR:{
            MODIFIER_VAR:None,
            BOUND_KEYWORD_VAR:keyword,
        }
    }

def make_create_closure(addr,value):
    return {
        CREATE_TAG:CREATE_TAG,
        DATA_ADDRESS_VAR:{NUMBER_TAG:addr},
        NUMBER_TAG:value,
    }

def make_assert_closure(addr,value):
    return {
        ASSERT_TAG:ASSERT_TAG,
        ASSERT_INNER_VAR:{
            DATA_ADDRESS_VAR:{
                NUMBER_TAG:addr,
            },
            NUMBER_TAG:value,
            VALUE_TAG:VALUE_TAG,
        }
    }

def make_adjustment_text(curr,target,up,down,wrap=None):
    adj_amt = abs(curr-target)
    adj = None
    if wrap is not None:
        wrap_up = abs(curr - wrap + 1) + abs(target)
        wrap_down = abs(target - wrap + 1) + abs(curr)
        if wrap_up < adj_amt:
            adj_amt = wrap_up
            adj = up
        elif wrap_down < adj_amt:
            adj_amt = wrap_down
            adj = down
    
    if adj is None:
        adj = up if target > curr else down
    return make_assembly_closure(adj*adj_amt)

def pack_keyword_closure(closure):
    return { INLINE_VAR:{ KEYWORD_VAR:closure } }

def bind_current_module(scope,module):
    bind_current_module_name(scope,module[NAME_TAG])
    # implicitly bind the module's bindings
    bind_module(scope,module[NAME_TAG]) 

def bind_current_module_name(scope,name):
    scope.bind(MODULE_INFO,name) # bind the module name to metadata

def bind_builtin_keywords(scope):
    for keyword in BUILTINS:
        bind_raw_text(keyword,[make_assembly_closure(BUILTINS[keyword])],scope)

def bind_raw_text(name,text,scope):
    # convert to the standard binding format
    binding = pack_into_binding_text(name,text)
    scope.bind(make_binding_var(name),binding)
    # add this keyword to the bound keywords for this scope
    with scope.use(KEYWORD_INFO) as bound:
        bound.add(name)

def bind_module(scope,name):
    # print("BINDING MODULE: {}".format(name))
    with scope.use(KEYWORD_INFO) as bound_list:
        mapping_info = scope.get(MAPPING_INFO)
        if name not in mapping_info:
            return
        for bname in mapping_info[name]:
            global_var = make_binding_var(bname,name)
            scoped_var = make_binding_var(bname)
            # print("BINDING {} to {}".format(global_var,scoped_var))

            # bind global definition into local definition
            scope.bind(scoped_var,scope.get(global_var))

            bound_list.add(bname)

def bind_layout_info(scope,info): # bind layout information into the scope
    scope.bind(make_layout_var(info[NAME_TAG]),int(info[NUMBER_TAG]))

def format_modifiers(modifier):
    text = ["("]

    def text_append(text,statement):
        if NAME_TAG in statement:
            text.append(statement[NAME_TAG])
        elif ASSEMBLY_TAG in statement:
            text.append(statement[ASSEMBLY_TAG])
        else:
            text.append(statement[NUMBER_TAG])

    text_append(text,modifier)
    if modifier[MODIFIER_CHAIN_VAR] is not None:
        for mod in modifier[MODIFIER_CHAIN_VAR]:
            text_append(text,mod)
    text.append(")")
    return " ".join(text)

def format_binding_def(binding):

    def text_append(text,statement):
        statement = statement[MODIFIER_ARG_VAR]
        sub = []
        if LAYOUT_TAG in statement:
            sub.append(LAYOUT_TAG)
        elif VALUE_TAG in statement:
            sub.append(VALUE_TAG)
        else:
            sub.append(TEXT_TAG)
        sub.append(statement[NAME_TAG])
        text.append(" ".join(sub))

    inner = []
    if binding[MODIFIER_DEC_VAR] is not None:
        for mod in binding[MODIFIER_DEC_VAR][MODIFIER_LIST_VAR]:
            text_append(inner,mod)

    return " ".join([binding[NAME_TAG],"(",", ".join(inner),")"])

def build_modifier_chain(modifiers):
    chain = []
    if modifiers[MODIFIER_CHAIN_VAR] is not None:
        for mod in [modifiers]+modifiers[MODIFIER_CHAIN_VAR]:
            if NAME_TAG in mod:
                chain.append((NAME_TAG,mod[NAME_TAG]))
            elif NUMBER_TAG in mod:
                chain.append((NUMBER_TAG,mod[NUMBER_TAG]))
            else:
                chain.append((ASSEMBLY_TAG,mod[ASSEMBLY_TAG]))
    return chain

# HELPER CLASSES ###############################################################

class Scope:
    def __init__(self,image=None,image_hook=None):
        self.defined = Stack()
        self.curr_symbols = set()
        self.symbols = {}
        self.image_hook = image_hook    

        if image:
            self.enter() # create the base scope automatically
            self.bind_image(image)

    def __str__(self):
        return pp.pformat(self.snapshot())

    def snapshot(self):
        values = {}
        for symbol in self.symbols:
            if len(self.symbols[symbol]):
                values[symbol] = self.symbols[symbol].peek()
        return values
                
    def has(self,symbol):
        return symbol in self.symbols and len(self.symbols[symbol]) > 0
    
    def get(self,symbol):
        if symbol not in self.symbols or not len(self.symbols[symbol]):
            raise KeyError("Symbol not in scope: {}".format(symbol))   
        return self.symbols[symbol].peek()

    def use(self,symbol):
        return ScopeCopyContextManager(self,symbol)

    def bind(self,symbol,value):
        if symbol in self.curr_symbols:
            self.symbols[symbol].swap(value)
        else:
            if symbol not in self.symbols:
                self.symbols[symbol] = Stack()
            self.symbols[symbol].push(value)
            self.curr_symbols.add(symbol)
        return value

    def unbind(self,symbol):
        if symbol not in self.curr_symbols:
            errstr = "Symbol {} not bound by current scope.".format(symbol)
            raise KeyError(errstr)
        self.symbols[symbol].pop()
        self.curr_symbols.remove(symbol)

    def partial(self,subset):
        return ScopePartialContextManager(self,subset)

    def bind_image(self,image):
        for symbol in image:
            self.bind(symbol,image[symbol])

    def inner(self):
        return ScopeContextManager(self)
    
    def enter(self):
        self.defined.push(self.curr_symbols.copy())
        self.curr_symbols = set()

    def exit(self):
        if not len(self.defined):
            raise IndexError("Exiting base scope")
        if self.image_hook:
            self.image_hook(self.snapshot())
        for symbol in self.curr_symbols:
            self.symbols[symbol].pop()
        self.curr_symbols = self.defined.pop()

class ScopeContextManager:
    def __init__(self,scope):
        self.scope = scope

    def __enter__(self):
        self.scope.enter()
        return self.scope

    def __exit__(self,exc_type,exc_value,traceback):
        self.scope.exit()

class ScopeCopyContextManager:
    def __init__(self,scope,symbol):
        self.scope = scope
        self.symbol = symbol
        self.hold = None

    def __enter__(self):
        # grab the symbol from the scope and make a copy
        self.hold = self.scope.get(self.symbol).copy()
        return self.hold

    def __exit__(self,exc_type,exc_value,traceback):
        # bind the value back into scope
        self.scope.bind(self.symbol,self.hold)

class ScopePartialContextManager:
    def __init__(self,scope,subset):
        self.scope = scope
        self.subset = subset
        self.rebind = set()
        self.lock = dict()

    def __enter__(self):
        for symbol in self.subset:
            if symbol in self.scope.curr_symbols:
                self.scope.curr_symbols.remove(symbol)
                self.rebind.add(symbol)
            if self.scope.has(symbol):
                self.lock[symbol] = len(self.scope.symbols[symbol]) 
            else:
                self.lock[symbol] = 0
            self.scope.bind(symbol,self.subset[symbol]) # rebind the subset
        return self.scope

    def __exit__(self,exc_type,exc_value,traceback):
        for symbol in self.subset:
            self.scope.unbind(symbol)
            if self.lock[symbol] != len(self.scope.symbols[symbol]):
                raise AssertionError("Improper subscope termination")
        for symbol in self.rebind: # rebind any symbols that were removed
            self.scope.curr_symbols.add(symbol)

class CopyList(list):
    def copy(self):
        return CopyList(self[:])
    def clear(self):
        while self:
            self.pop()

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
                if token[0] == COMMENT_DELIM:
                    break
                yield token
            self.line = self.line + 1

# TOP LEVEL COMPILE ############################################################

def compile_module(source,dest):
    with open("cow.json","r") as src:
        g = Grammar.create(json.loads(src.read()))

    parser = ParsingAutomaton("PARSER",g)
    path = str.split(source,"/")
    root_module_name = path.pop().split(".")[0]

    module = module_loader(root_module_name,parser,path)

    text = build(module,parser,path)
    
    with open(dest,"w") as target:
        for string in text:
            target.write(string)
            target.write('\n')
    
handler = BCCErrorHandler()

def main():
    if len(sys.argv) < 3:
        print("usage: bcc cow_file beef_file")
    cow = sys.argv[1]
    beef= sys.argv[2]
    compile_module(cow,beef)
        
if __name__ == '__main__':
    main()