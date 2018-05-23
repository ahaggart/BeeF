#!/usr/bin/env python2.7
"""
    Proper CFG parser
"""
from __future__ import print_function
import sys
import re
import pprint
import json
import sets

pp = pprint.PrettyPrinter(indent=1)

# FORMAT KEYWORDS
TERMINALS_KEY   = "terminals"
GENERICS_KEY    = "generics"
RULES_KEY       = "rules"
START_KEY       = "start"

# INTERNAL KEYWORDS
META_START_KEY      = "_META_START_"
META_META_START_KEY = "_META_META_START_"

# TAGS
EPSILON_T       = "_EPSILON_"
ID_T            = "_ID_"
ACCEPT_T        = "_ACCEPTING_"
REDUCTION_T     = "_REDUCTION_"
EXPANDED_T      = "_EXPANDED_"
SHIFT_T         = "_SHIFT_"
GO_T            = "_GO_"
REJECT_T        = "_REJECT_"

SYMBOL_I        = 0
STATE_I         = 1
TREE_I          = 2

VERBOSE = False

# lazily evaluated set nesting framework, for recursively building token sets
# with interdependecnies
class SuperSet:
    def __init__(self,symbol,subsets=[]):
        self.symbol = symbol
        self.subsets = []
        for subset in subsets:
            self.add(subset)

    def __iter__(self,pending=None): # recursively generate this set's elements
        if not pending:
            pending = set()
        # print("starting evaluation of subset: {} with pending: {}".format(self.symbol,pending))
        pending.add(self.symbol)

        for subset in self.subsets:
            if subset.__class__.__name__ != "SuperSet": # pull everything from base sets
                for item in subset:
                    yield item
            elif subset.symbol not in pending:
                # print("Evaluating {} as subset of {}".format(subset.symbol,self.symbol))
                for item in subset.__iter__(pending):   # recusively resolve
                    # print("Subset: {}\tElem: {}".format(subset.symbol,item))
                    yield item
            else:
                # print("Threw out circular dep {} from evaluation of {}".format(subset.symbol,self.symbol))
                pass
        # print("finished evaluation of subset: {}".format(self.symbol))

    def add(self,subset):
        if subset.__class__.__name__ != "SuperSet":
            self.subsets.append(subset)
        elif subset.symbol != self.symbol:
            # print("Added {} as subset of {}".format(subset.symbol,self.symbol))
            self.subsets.append(subset)

def pivot(table):
    return dict([(table[k],k) for k in table])

class Stack(list):
    def push(self,x):
        self.append(x)
    
    def peek(self):
        if len(self):
            return self[len(self)-1]
        raise IndexError,"Peeking empty stack"
    
    def swap(self,value):
        if not len(self):
            raise IndexError,"Swapping empty stack"
        self[len(self)-1] = value

class Grammar:
    def __init__(self,nonterminals,generics,rules,start):
        self.start          = start
        self.nonterminals   = dict([(nont.symbol,nont) for nont in nonterminals])
        self.rules          = dict([(rule.symbol,rule) for rule in rules])
        self.generics       = generics

        if not self.start.symbol in self.nonterminals:
            parse_error("Invalid start variable: {}".format(self.start))

    @staticmethod
    def create(source):
        # TODO: do the class packing in the classes themselves?
        terminals   = set(Terminal(term) for term in source[TERMINALS_KEY])
        generics    = source[GENERICS_KEY]
        generics    = dict([
            (name,re.compile(generics[name])) for name in generics
        ])
        full_syms   = set(source[TERMINALS_KEY])
        full_syms.update(generics.keys())
        rules,nt    = Rule.create(source[RULES_KEY],full_syms)
        nonterminals= [ Nonterminal(sym) for sym in nt ]
        start       = Nonterminal(source[START_KEY])
        g = Grammar(nonterminals,generics,rules,start)
        g.follow() # compute the follow sets
        return g

    def follow(self):
        self.nonterminals[META_START_KEY] = Nonterminal(META_START_KEY)
        self.nonterminals[META_META_START_KEY] = Nonterminal(META_META_START_KEY)
        self.rules[META_START_KEY] = Rule(META_START_KEY,[Derivation(META_START_KEY,[self.start,ParseTerminator()])])
        self.rules[META_META_START_KEY] = Rule(META_META_START_KEY,[Derivation(META_META_START_KEY,[self.nonterminals[META_START_KEY],ParseTerminator()])])
        for rulename in self.rules:
            for der in self.rules[rulename]:
                for subexp in der.subexpressions():
                    if subexp.token.symbol not in self.nonterminals:
                        # print("terminal: {}".format(subexp.token.symbol))
                        continue

                    # grab the corresponding nonterminal from the dictionary
                    ss = self.nonterminals[subexp.token.symbol].follow
                    if subexp.succ == None:
                        ss.add(self.nonterminals[rulename].follow)
                        continue
                    # print("{}: {}".format(subexp.succ.symbol,subexp.succ.first(self.rules)))
                    ss.add(subexp.succ.first(self.rules))
                    if subexp.succ.nullable(self.rules):
                        if rulename != subexp.token.symbol:
                            # print([symbol.token.symbol for symbol in subexp.succ])
                            # print("added {} as follow subset of {}".format(rulename,ss.symbol))
                            ss.add(self.nonterminals[rulename].follow)
                    # for symbol in subexp:
                    #     print("{},".format(symbol.symbol.symbol),end="") # lol
                    # print("")

    def parse(self,string):
        # do preoprocessing on the grammar structure

        # use a parsing strategy LL(1), SLR, LALR, etc
        # need more research, probably SLR
        pass

class Expression:
    def __init__(self,symbol,symbols):
        self.symbol = symbol
        self.symbols = symbols
        self.is_nullable = None
        self.first_symbol = None

    def __iter__(self):
        for symbol in self.symbols:
            yield symbol

    def nullable(self,rules,pending=None):
        if pending == None:
            pending = set()
        if self.is_nullable == None:
            pending.add(self.symbol)
            self.is_nullable = all(self._nullables(rules,pending))
        return self.is_nullable
    def _nullables(self,rules,pending):
        for symbol in self:
            if symbol.symbol not in pending:
                yield symbol.nullable(rules,pending)

    def first(self,rules,pending=None):
        if pending == None:
            pending = set()
        if self.first_symbol == None:
            pending.add(self.symbol)
            self.first_symbol = set()
            for symbol in self:
                self.first_symbol.update(symbol.first(rules,pending))
                if not symbol.nullable(rules,set()):
                    break
        return self.first_symbol

class SubExpression(Expression):
    def __init__(self,symbol,succ=None):
        self.token = symbol
        Expression.__init__(self,self.token.symbol,[])
        self.succ = succ

    def __iter__(self): # recursively generate this subexpression's token chain
        yield self
        if self.succ:
            for symbol in self.succ:
                yield symbol

    def _nullables(self,rules,pending): # generate nullability of whole token chain
        for symbol in self:
            yield symbol.token.nullable(rules,pending)

    def first(self,rules,pending=None):
        if pending == None:
            pending = set()
        if self.first_symbol == None:
            pending.add(self.symbol)
            self.first_symbol = set()
            for symbol in self:
                self.first_symbol.update(symbol.token.first(rules,pending))
                if not symbol.token.nullable(rules,set()):
                    break
        return self.first_symbol
        


class Derivation(Expression):
    def __init__(self,symbol,symbols):
        Expression.__init__(self,symbol,symbols)

    @staticmethod
    def create(symbol,source,terminals,nonterminals):
        tokens = []
        for symbol in str.split(str(source).strip()," "):
            if symbol in terminals:
                tokens.append(Terminal(symbol))
            elif symbol in nonterminals:
                tokens.append(Nonterminal(symbol))
            else:
                parse_error("Unspecified symbol in rule: {}".format(symbol))
        return Derivation(symbol,tokens)

    def subexpressions(self):
        first = False
        pred = None
        for symbol in self.symbols:
            if first:
                pred.succ = SubExpression(symbol)
                pred = pred.succ
            else:
                pred = SubExpression(symbol)
                first = pred
        while(first.succ):
            yield first
            first = first.succ
        yield first

    def reduce(self,stack,generics):
        symbols = self.symbols[:]
        tree = None
        # print("Reducing: {}".format(self.symbol))
        while symbols:
            if tree == None:
                tree = {}
            top = stack.pop()
            actual = str(top[SYMBOL_I])
            expected = str(symbols.pop())
                
            if expected in generics:
                if generics[expected].match(actual) == None:
                    parse_error("Failed to match generic symbol {} to {}".format(
                        expected,actual
                    ))

                # handle duplicate generics by placing them in a list
                # maintins ordering of elements
                if expected in tree:
                    if tree[expected].__class__.__name__ != "list":
                        tree[expected] = [tree[expected]]
                    tree[expected].insert(0,actual)
                else:
                    tree[expected] = actual
            elif expected != actual:
                # print("{} == {} : {}".format(expected,actual,expected==actual))
                parse_error("Expected symbol in reduction: \"{}\"\nGot: \"{}\"".format(
                    expected,actual))
            else:
                tree[expected] = top[TREE_I]
        return tree

    # build a simple NFA representing this derivation
    def make_NFA(self,id):
        start_state  = ParsingNFAState()
        curr_state = start_state
        table = [start_state]

        # add a transition and state for each token
        for symbol in self:
            new_state = ParsingNFAState()
            curr_state.add(symbol.symbol,len(table))
            table.append(new_state)
            curr_state = new_state
            if symbol.__class__.__name__ != "Nonterminal":
                curr_state.tag(SHIFT_T,symbol.symbol)
        
        curr_state.make_accepting()
        # tag the accept state with a reduction
        curr_state.tag(REDUCTION_T,(self.symbol,id))
        curr_state.untag(SHIFT_T)
        
        return ParsingNFA(self.symbol,table)



class Nonterminal:
    def __init__(self,symbol):
        self.symbol = symbol
        self.is_nullable = None
        self.first_symbol = None   
        self.follow = SuperSet(self.symbol)

    def __str__(self):
        return self.symbol

    def nullable(self,rules,pending=None):
        if pending == None:
            pending = set()
        if self.is_nullable == None:
            if self.symbol not in rules:
                parse_error("No rule for nonterminal: " + self.symbol)
            pending.add(self.symbol)
            self.is_nullable = any(rules[self.symbol]._nullables(rules,pending))
        return self.is_nullable

    def first(self,rules,pending=None):
        if pending == None:
            pending = set()
        if self.first_symbol == None:
            if self.symbol not in rules:
                parse_error("No rule for nonterminal: " + self.symbol)
            self.first_symbol = set()
            pending.add(self.symbol)
            self.first_symbol.update(rules[self.symbol].first(rules,pending))
        else:
            # print("got cached start tokens for: {}".format(self.symbol))
            pass
        return self.first_symbol
            

class Rule:
    def __init__(self,symbol,derivations):
        self.symbol      = symbol
        self.derivations = derivations
        for derivation in self.derivations:
            derivation.symbol = self.symbol

    def __iter__(self):
        for derivation in self.derivations:
            yield derivation

    @staticmethod
    def create(source,terminals):
        # expect a dict of nonterm->term
        # we will build the symbol sets for nonterms
        nonterms = set([symbol for symbol in source])
        rules = []
        for symbol in source:
            ders = []
            for derivation in source[symbol]:
                if derivation == None:
                    ders.append(Epsilon(symbol))
                    continue
                ders.append(Derivation.create(symbol,derivation,terminals,nonterms))
            rules.append(Rule(symbol,ders))
        return rules,nonterms

    def _nullables(self,rules,pending):
        if not self.derivations:
            parse_error("Nonterminal has no derivations: "+self.symbol)
        for derivation in self.derivations:
            yield derivation.nullable(rules,pending)

    def first(self,rules,pending=None):
        if pending == None:
            pending = set()
        first = set()
        for derivation in self.derivations:
            first.update(derivation.first(rules,pending))
        return first

    def make_NFA(self):
        count = 0
        der_nfas = []
        for der in self.derivations:
            nfa = der.make_NFA(count)
            der_nfas.append(nfa)
            count = count + 1
        
        # group derivation NFAs into aggregate NFA
        agg = ParsingNFA(
            self.symbol,
            [ParsingNFAState()])
        
        # agg.table[1].tags.add((REDUCTION_T,self.symbol,-1))

        for nfa in der_nfas:
            nfa.link(agg,agg.start) 
        
        return agg       

class Terminal:
    def __init__(self,symbol):
        self.symbol = symbol
    def nullable(self,rules,pending=None):
        return False
    def first(self,rules,pending=None):
        return set([self.symbol])
    def __str__(self):
        return self.symbol

class Generic(Terminal):
    def __init__(self,symbol,regex):
        Terminal.__init__(self,symbol)

    def check(self,symbol):
        # check if a symbol matches the pattern for this generic symbol
        return False

class ParseTerminator(Terminal):
    def __init__(self):
        Terminal.__init__(self,"$")

class Epsilon: # we might not need this
    def __init__(self,symbol):
        self.symbol = symbol
        self.symbols = ()
    def nullable(self,rules,pending=None):
        return True
    def first(self,rules,pending=None):
        return set()
    def subexpressions(self):
        return []
    def make_NFA(self,id):
        state = ParsingNFAState(accept=True)
        state.tag(REDUCTION_T,(self.symbol,id))
        return ParsingNFA(EPSILON_T,[state])
    def reduce(self,stack,generics):
        return None

# parse input token-by-token, using parse table to decide action and state
class ParsingAutomaton:
    def __init__(self,name,grammar):
        self.name           = name
        self.grammar        = grammar
        self.action_table   = []
        self.dfa            = None
        self.build()

    def act(self,stack,tree,backlog,token,action_data):
        action = action_data[0]
        data = action_data[1]
        # print(action_data)
        if action == GO_T:
            return self.go(stack,tree,backlog,token)
        elif action == REDUCTION_T:
            return self.reduce(stack,tree,backlog,token,data)
        elif action == SHIFT_T:
            return self.shift(stack,tree,backlog,token)
        elif action == ACCEPT_T:
            return self.accept(stack,tree,backlog,token)
        elif action == REJECT_T:
            return self.reject(stack,tree,backlog,token)
        else:
            parse_error("Invalid action?")

    def reduce(self,stack,tree,backlog,token,data):
        nt = data[0]
        red_id = data[1]
        # print(nt)
        # print(red_id)
        tree = self.grammar.rules[nt].derivations[red_id].reduce(stack,self.grammar.generics)

        # push the nonterminal to the backlog
        backlog.push(token)
        backlog.push(nt)

        # make the current tree a subtree of the next tree
        # print("DFA before:")
        # pp.pprint(self.dfa.table[self.dfa.state])
        # stack.peek()[TREE_I][nt] = tree
        self.dfa.state = stack.peek()[STATE_I]
        # print("DFA after:")
        # pp.pprint(self.dfa.table[self.dfa.state])
        # print("TREE:")
        # pp.pprint(tree)
        return tree,False

    def go(self,stack,tree,backlog,token):
        stack.push((token,self.dfa.state,tree))
        return tree,False

    def shift(self,stack,tree,backlog,token):
        stack.push((token,self.dfa.state,token))
        return {},False

    def accept(self,stack,tree,backlog,token):
        print("accepted")
        stack.pop()
        tree = stack.pop()[TREE_I]
        return tree,True

    def reject(self,stack,tree,backlog,token):
        print("rejected")
        return tree,True    

    def parse(self,tokenizer):
        try:
            return self._parse(tokenizer)
        except ParseError as e:
            line = tokenizer.getLine()
            file = tokenizer.getFile()
            raise ParseError("{}: Line {}: {}".format(
                file,line,e.message))

    def _parse(self,tokens):
        # print("PARSING:")
        # pp.pprint(self.dfa.table)
        processed = []
        tree = {}
        working_tree = tree
        stack = Stack(("base",0,{}))
        stack.push(("root",0,tree))
        backlog = Stack()
        self.dfa.reset()

        tokens.append("$")
        tokens.append("$")

        done = False
        for token in tokens:
            while backlog: # parse the nonterminal backlog first
                nt = backlog.pop()
                # print(nt)
                working_tree,done = self.process(stack,working_tree,backlog,nt)
                # print()
                if done:
                    break                
            if done:
                break 
            # print(token)
            working_tree,done = self.process(stack,working_tree,backlog,token)
            processed.append(token)
            # pp.pprint(tree)
            # print()
            if done:
                break 
            
        working_tree.pop("$")
        # pp.pprint(working_tree)
        return working_tree

    def process(self,stack,tree,backlog,token):
        old_state = self.dfa.state
        p = self.dfa.process(token)
        sym = token
        matched = False
        if p != None: # DFA rejected, try generics
            for sym in p:
                if sym in self.grammar.generics:
                    if self.grammar.generics[sym].match(token):
                        matched = True
                        # print("Matched {} to {}".format(token,sym))
                        self.dfa.process(sym) # use the generic symbol
                        break                
            if not matched:
                sym = token
                for action in self.action_table[old_state]:
                    if action in self.grammar.generics:
                        if self.grammar.generics[action].match(token):
                            # print("Matched {} to {}".format(token,action))
                            matched = True
                            sym = action
                            break

        if sym in self.action_table[old_state]:
            return self.act(stack,
                            tree,
                            backlog,
                            token,
                            self.action_table[old_state][sym])
        elif not matched:
            context,sugg = self.get_context(stack)
            context_msg = "During expansion of: {}".format(context)
            sugg_msg = "Perhaps you meant: {}?".format(sugg)
            parse_error("Unable to match symbol: \"{}\"\n{}\n{}".format(
                token,context_msg,sugg_msg))
        return tree,False

    def get_context(self,stack): # destructive
        if not stack:
            return "base"
        state = stack[-1][1]
        table = self.nfa.table
        sugg = set()
        context = []
        for nfa_state in self.mapping[state]:
            if REDUCTION_T in table[nfa_state].tags:
                reduction = table[nfa_state].tags[REDUCTION_T][0]
                context.append(reduction)
                sugg.update(self.grammar.nonterminals[reduction].follow)
        sugg_tokens = [format_token(tk,self.grammar) for tk in sugg]
        return ' or '.join(context),' or '.join(sugg_tokens)

    def build(self):
        nfas = {}
        for rule in self.grammar.rules:
            nfas[rule] = self.grammar.rules[rule].make_NFA()

        # combine the NFAs for each rule into one big NFA
        base = nfas.pop(META_META_START_KEY)
        offsets = {}
        for name in nfas:
            nfa = nfas[name]
            offset = base.insert(nfa)
            offsets[name] = (offset,offset+1)

        while( # I love python
            any([base.link_internal(name,offsets[name][0],offsets[name][1]) 
                for name in offsets ])):
            continue # loop until there are no successful link attempts

        parser,mappings = base.determine()
        parse_table = parser.table # build a DFA with the parse table

        follows = follow(self.grammar)

        state_to_superstate = pivot(mappings)

        slr_con_msg = "SLR Table Conflict:\n{} for {}\n>> in: {}"

        for state in range(0,len(parse_table)):
            actions = {}
            self.action_table.append(actions)
            superstate = state_to_superstate[state]

            if state in parser.accepts:
                action = None
                for s in superstate:
                    tags = base.table[s].tags
                    if REDUCTION_T in tags and ACCEPT_T in tags:
                        if action != None:
                            parse_error(slr_con_msg.format(
                                action,state,parser.table[state]))
                        action = tags[REDUCTION_T]
                if action:
                    if action[0] == META_META_START_KEY:
                        actions["$"] = (ACCEPT_T,("null",-1))
                    else:
                        for tk in follows[action[0]]:
                            actions[tk] = (REDUCTION_T,(action[0],action[1]))
            for tr in parser.table[state]:
                if tr in actions:
                    parse_error(slr_con_msg.format(
                        actions[tr],tr,parser.table[state]))
                if tr in self.grammar.nonterminals:
                    actions[tr] = (GO_T,-1)
                else:
                    actions[tr] = (SHIFT_T,-1)

        self.mapping = state_to_superstate
        self.nfa = base
        self.dfa = parser         
        return parser

class ParsingDFA:
    def __init__(self,name,table,accepts):
        self.table  = table
        self.name   = name
        self.accepts = accepts
        self.start  = 0
    
    def parse(self,tokens):
        self.state = self.start
        for token in tokens:
            p = self.process(token)
            if p != None:
                return p
        self.accept()

    def process(self,token):
        if token not in self.table[self.state]:
            self.reject(token)
            return self.table[self.state]
        self.state = self.table[self.state][token]

    def reject(self,token):
        # print("{} rejected on: {}".format(self.name,token))
        # pp.pprint(self.table[self.state])
        pass


    def accept(self):
        # print("Accepted input. Finished in state: {}".format(self.state))
        # pp.pprint(self.table[self.state])
        pass

    def reset(self):
        self.state = self.start

class ParsingNFAState:
    def __init__(self,accept=False):
        self.transitions    = {}
        self.epsilons       = set()
        self.tags           = {}
        if accept:
            self.make_accepting()

    def make_accepting(self):
        self.tag(ACCEPT_T)
    
    def add(self,token,dest):
        if token == None:
            self.epsilons.add(dest)
            return
        if token not in self.transitions:
            self.transitions[token] = set()
        self.transitions[token].add(dest)

    def tag(self,key,value=None):
        self.tags[key] = value

    def untag(self,key):
        if key in self.tags:
            return self.tags.pop(key)
        return None

    def shift_table(self,shamt):
        self.remap(lambda tid:tid+shamt)
    
    def copy(self):
        copy = ParsingNFAState()
        copy.transitions    = self.transitions.copy()
        copy.epsilons       = self.epsilons.copy()
        copy.tags           = self.tags.copy()
        return copy

    def remap(self,mapfn):
        for t in self.transitions:
            self.transitions[t]= set([mapfn(tid) for tid in self.transitions[t]])
        self.epsilons =  set([mapfn(eid) for eid in self.epsilons])

class ParsingNFA:
    def __init__(self,name=None,table=None):
        self.name = name
        if not table:
            table = [ParsingNFAState()]
        self.table = table
        self.start = 0 # start state is always id 0
        self.accept = None
        self.find_accepting()

    def __str__(self):
        count = 0
        base = "{} (NFA):\n".format(self.name)
        for item in self.table:
            mark = ""
            if count == 0:
                mark = mark + "s"
            if ACCEPT_T in item.tags:
                mark = mark + "a"
            base = base + "{}:{}".format(count,mark)
            for token in item.transitions:
                base = base + "\t{} -> {}".format(token,item.transitions[token])
                base = base + "\n"
            if item.epsilons:
                base = base + "\t\Epsilon -> {}".format(item.epsilons)
                base = base + "\n"
            if not item.transitions and not item.epsilons:
                base = base + '\n'
            count = count + 1
        return base

    def __len__(self):
        return len(self.table)

    def copy(self):
        return ParsingNFA(self.name,[s.copy() for s in self.table])

    def shift_table(self,shamt):
        for item in self.table:
            item.shift_table(shamt)

    def extend(self,other):
        self.table.extend(other.table)
        self.find_accepting()

    def find_accepting(self):
        self.accept = set([
            i for i in range(0,len(self.table)) 
            if ACCEPT_T in self.table[i].tags
        ])

    def remove_self_refs(self):
        for entry in self.table:
            if self.name in entry.transitions:
                # remove the "circular" ref
                dest = entry.transitions[self.name]
                del entry.transitions[self.name]

                # add a real circular ref
                entry.epsilons.add(self.start)

                # add a real circular ref
                entry.epsilons.add(self.start)
                for tid in dest:
                    entry.epsilons.add(tid)
            else:
                pass

    # replace a transition with a link
    def link_internal(self,token,start,end):
        linked = False
        for index in range(0,len(self)):
            item = self.table[index]
            if token in item.transitions and EXPANDED_T not in item.tags:
                linked = True
                # link transition to the location where we are inserting
                self.table[index].add(None,start)   # add new location
                self.table[index].tag(EXPANDED_T)
        if not linked:
            return False
        return True

    def insert(self,other):
        other_start = len(self)
        other.shift_table(other_start)
        self.extend(other)
        return other_start

    def link(self,other,start_id):
        # offset table entries
        self.shift_table(len(other))
        other.table[start_id].epsilons.add(len(other))   # add new location

        other.extend(self)    # extend the result NFA with the linked copy

    # garbage collect this NFA
    # returns a new NFA with no unreachable states
    # will not affect DFA produced by determine()
    def gc(self):
        reachable = set()
        added = set([self.start])
        while len(added) > 0:
            dests = self._collect_destinations(added)
            # print(dests)
            old_added = added
            added = set()
            for token in dests:
                added.update(dests[token])
            added.update(self._collect_reachable(old_added))
            added = added - reachable
            reachable.update(added)

        id_map = {}
        new_table = []
        for i in range(0,len(self.table)):
            if i in reachable:
                id_map[i] = len(new_table)
                new_table.append(self.table[i].copy())
            else:
                # print("unreachable: {}".format(i))
                pass

        for item in new_table:
            item.remap( lambda tid:id_map[tid] )

        return ParsingNFA(self.name,new_table)

    def determine(self): # convert this NFA into a DFA
        table = {}
        accepts = set()
        start_super = self._collect_reachable([self.start])
        to_add = set([start_super])

        while len(to_add) != 0:
            new_add = set()
            for superstate in to_add:
                # add this superstate to table if not there already
                table[superstate] = self._collect_destinations(superstate)
                for token in table[superstate]:
                    dest = table[superstate][token]
                    if dest not in table:
                        new_add.add(dest)
            to_add = new_add

        # iterate over the table and build a completely determined table
        # build a table of state ids
        table_ids = { start_super:0 }
        count = 0
        for state in table:
            if state == start_super:
                continue
            count = count + 1
            table_ids[state] = count
            if state & self.accept: # intersection of superstate and accepting
                accepts.add(count)

        # iterate over table and resolve frozen sets into table indices
        sorted_table = [0]*(count+1)
        for state in table:
            transitions = dict([
                    # pair token to the id assigned to the destination state
                    (token,table_ids[table[state][token]]) # k-v pair  
                    for token in table[state]
            ])
            sorted_table[table_ids[state]] = transitions

        # return the DFA table and the id table
        # caller may have metadata to attach based on superstate composition
        return ParsingDFA(self.name,sorted_table,accepts),table_ids


    def _collect_reachable(self,start_set):
        working_set = set(start_set)
        ws_size = 0
        # collect epsilon-reachable states
        while ws_size != len(working_set):
            ws_size = len(working_set)
            ws_copy = working_set.copy()
            for state in ws_copy:
                working_set.update(self.table[state].epsilons)
        return frozenset(working_set) # use this as a superset table entry

    def _collect_destinations(self,states):
        # collect listed transition tokens
        tokens = set()
        for state in states:
            tokens.update(self.table[state].transitions.keys())

        dest_sets = {}
        for token in tokens:
            dest_sets[token] = set()
            for state in states:
                if token in self.table[state].transitions:
                    dest_sets[token].update(self.table[state].transitions[token])
            dest_sets[token] = self._collect_reachable(dest_sets[token])
        return dest_sets

class Util:
    # identify self-nesting nonterminals and un-nest them into a list
    # list ordering depends on the recursion type
    # left-recursive nonterminals will reverse the order in the list
    # right-recursive nonterminals will maintain the order in the list
    @staticmethod
    def unroll(tree,grammar):
        # for var in Util.collect_recursive(tree):
        for var in Util.collect_recursive(grammar):
            tree = Util._unroll(tree,var,Util.left_recursive(var,grammar))
        return tree

    @staticmethod
    # def collect_recursive(tree,acc=None):
    #     if acc == None:
    #         acc = set()
    #     for var in tree:
    #         if tree[var].__class__.__name__ == "dict":
    #             if var in tree[var]:
    #                 acc.add(var)
    #             acc.update(Util.collect_recursive(tree[var],acc))
    #     return acc

    def collect_recursive(grammar):
        for nt in grammar.rules:
            for derivation in grammar.rules[nt]:
                done = False
                for symbol in derivation.symbols:
                    if symbol.symbol == nt:
                        yield nt
                        done = True
                    if done:
                        break
                if done:
                    break

    @staticmethod
    def _unroll(tree,variable,reverse=False):
        # "unroll" a recursively expanding variable
        if tree.__class__.__name__ != "dict":
            if tree.__class__.__name__ == "list":
                return [Util._unroll(item,variable,reverse) for item in tree]
            return tree
        if variable in tree and tree[variable] != None:
            sub = tree[variable]                
            unrolled = []
            tree[variable] = unrolled
            if sub.__class__.__name__ == "list":
                tree[variable] = sub
                sub = None
            while sub != None:
                tmp  = sub.pop(variable) if variable in sub else None
                unrolled.append(Util._unroll(sub,variable,reverse))
                sub = tmp
            if reverse:
                unrolled.reverse()
        return dict([(name,Util._unroll(tree[name],variable,reverse)) for name in tree])

    @staticmethod
    def left_recursive(var,grammar):
        errstr = "Recursion check not valid for: {}".format(var)
        assert var in grammar.nonterminals, errstr
        rule = grammar.rules[var]
        err = True
        for der in rule:
            # print("checking: {}".format(der.symbols))
            if not len(der.symbols):
                continue
            if der.symbols[len(der.symbols)-1].symbol == var:
                if err:
                    rec_type = False
                    err = False
                elif rec_type:
                    err = True
                    break
            elif der.symbols[0].symbol == var:
                if err:
                    rec_type = True
                    err = False
                elif not rec_type:
                    err = True
                    break        
        if not err:
            return rec_type
        errstr2 = "Could not determine recursion type for: {}".format(var)
        raise ValueError(errstr2)

        
# produce a dictionary(variable->terminal) of the first terminals in strings
# generated by each variable
def first(grammar):
    firsts = dict()
    for nt in grammar.nonterminals:
        nonterm = grammar.nonterminals[nt]
        firsts[nonterm.symbol] = nonterm.first(grammar.rules) 
    return firsts

# produce a set(variable) of variables that can generate the empty string
def nullable(grammar):
    nullables = set()
    for nt in grammar.nonterminals:
        nonterm = grammar.nonterminals[nt]
        if nonterm.nullable(grammar.rules):
            nullables.add(nonterm.symbol)
    return nullables
            
def follow(grammar):
    follows = dict()
    for nt in grammar.nonterminals:
        nonterm = grammar.nonterminals[nt]
        follows[nonterm.symbol] = set([follow for follow in nonterm.follow])
    return follows

def format_token(token,grammar):
    if token in grammar.generics:
        return "\"<generic {}>\"".format(token)
    else:
        return "\"{}\"".format(token)

class ParseError(Exception):
    def __init__(self,message):
        self.message = message

    def __str__(self):
        return self.message
    

def parse_error(reason):
    raise ParseError("Error: {}".format(reason))