#!/usr/bin/env python2.7
"""
    Proper CFG parser
"""
from __future__ import print_function
import sys
import pprint as pp
import json
import sets

TERMINALS_KEY = "terminals"
GENERICS_KEY  = "generics"
RULES_KEY     = "rules"
START_KEY     = "start"
META_START_KEY = "_META_START_"
EPSILON_T = "_EPSILON_"
ID_T = "_ID_"
ACCEPT_T = "_ACCEPTING_"
REDUCTION_T = "_REDUCTION_"

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

class Grammar:
    def __init__(self,nonterminals,rules,start):
        self.start          = start
        self.nonterminals   = dict([(nont.symbol,nont) for nont in nonterminals])
        self.rules          = dict([(rule.symbol,rule) for rule in rules])
        self.start          = start

        if not self.start.symbol in self.nonterminals:
            parse_error("Invalid start variable: {}".format(self.start))

    @staticmethod
    def create(source):
        # TODO: do the class packing in the classes themselves?
        terminals   = set(Terminal(term) for term in source[TERMINALS_KEY])
        generics    = set(source[GENERICS_KEY])
        full_syms   = set(source[TERMINALS_KEY])
        full_syms.update(generics)
        rules,nt    = Rule.create(source[RULES_KEY],full_syms)
        nonterminals= [ Nonterminal(sym) for sym in nt ]
        start       = Nonterminal(source[START_KEY])
        g = Grammar(nonterminals,rules,start)
        return g

    def follow(self):
        self.nonterminals[META_START_KEY] = Nonterminal(META_START_KEY)
        self.rules[META_START_KEY] = Rule(META_START_KEY,[Derivation(META_START_KEY,[self.start,ParseTerminator()])])
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
        
        curr_state.make_accepting()
        # tag the accept state with a reduction
        curr_state.tags.add((REDUCTION_T,self.symbol,"{}_{}".format(self.symbol,id)))
        
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
                    ders.append(Epsilon())
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
            [ParsingNFAState(),ParsingNFAState(accept=True)])
        
        # agg.table[1].tags.add((REDUCTION_T,self.symbol,-1))

        for nfa in der_nfas:
            nfa.link(agg,agg.start,1) 
        
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
    def nullable(self,rules,pending=None):
        return True
    def first(self,rules,pending=None):
        return set()
    def subexpressions(self):
        return []
    def make_NFA(self,id):
        state = ParsingNFAState(accept=True)
        state.tags.add((REDUCTION_T,EPSILON_T,"{}_{}".format(EPSILON_T,id)))
        return ParsingNFA(EPSILON_T,[state])

class ParsingAction:
    def __init__(self,triggers,action):
        self.triggers   = triggers
        self.action     = action

    def __str__(self):
        return "{"+str.join(",",["\""+str(t)+"\"" for t in self.triggers])+"}} -> {}".format(self.action)

    def __repr__(self):
        return self.__str__()

# parse input token-by-token, using parse table to decide action and state
class ParsingAutomaton:
    def __init__(self,name,grammar):
        self.name = name
        self.grammar = grammar
        self.actions = {}

    def build(self):
        nfas = {}
        for rule in self.grammar.rules:
            nfas[rule] = self.grammar.rules[rule].make_NFA()

        # combine the NFAs for each rule into one big NFA
        base = nfas.pop(META_START_KEY)
        offsets = {}
        for name in nfas:
            nfa = nfas[name]
            offset = base.insert(nfa)
            offsets[name] = (offset,offset+1)

        while( # I love python
            any([base.link_internal(name,offsets[name][0],offsets[name][1]) 
                for name in offsets ])):
            continue # loop until there are no successful link attempts

        parse_table,mappings = base.determine()
        parser = ParsingDFA(self.name,parse_table) # build a DFA with the parse table

        # grab the follow sets for the grammar
        follows = follow(self.grammar)

        # extract reduction information from mapping table
        reduction_table = {}
        for superstate in mappings:
            idx = mappings[superstate]
            for state in superstate:
                # if ACCEPT_T not in base.table[state].tags:
                #     continue
                for tag in base.table[state].tags:
                    if tag == ACCEPT_T:
                        continue
                    if tag[0] == REDUCTION_T:
                        if tag[1] == EPSILON_T:
                            continue
                        if idx not in self.actions:
                            self.actions[idx] = []
                        self.actions[idx].append(ParsingAction(
                            follows[tag[1]],tag[2]
                        ))
        for i in range(0,len(parse_table)):
            if i in self.actions:
                self.actions[i].insert(0,parse_table[i])
                # self.actions[i].append(0,parse_table[i])
        pp.pprint(self.actions)
                        

        return parser

class ParsingDFA:
    def __init__(self,name,table):
        self.table  = table
        self.name   = name
        self.start  = 0
    
    def parse(self,tokens):
        self.state = self.start
        for token in tokens:
            if self.process(token) == -1:
                return
        self.accept()

    def process(self,token):
        if token not in self.table[self.state]:
            self.reject(token)
            return -1
        self.state = self.table[self.state][token]
        return self.state

    def reject(self,token):
        print("{} rejected on: {}".format(self.name,token))
        pp.pprint(self.table[self.state])


    def accept(self):
        print("Accepted input. Finished in state: {}".format(self.state))
        pp.pprint(self.table[self.state])
            

# use tuples of (token,boolean) to denote transitions
# (token,False) denotes a nonterminal transition
class ParsingNFAState:
    def __init__(self,accept=False):
        self.transitions    = {}
        self.epsilons       = set()
        self.tags           = set()
        if accept:
            self.make_accepting()

    def make_accepting(self):
        self.tags.add(ACCEPT_T)
    
    def add(self,token,dest):
        if token == None:
            self.epsilons.add(dest)
            return
        if token not in self.transitions:
            self.transitions[token] = set()
        self.transitions[token].add(dest)

    def shift_table(self,shamt):
        # for t in self.transitions:
        #     self.transitions[t]= set([tid+shamt for tid in self.transitions[t]])
        # self.epsilons =  set([eid+shamt for eid in self.epsilons])
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
        self.remove_self_refs()

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
        self.remove_self_refs()

    def find_accepting(self):
        self.accept = set([
            i for i in range(0,len(self.table)) 
            if ACCEPT_T in self.table[i].tags
        ])

    def remove_self_refs(self):
        for entry in self.table:
            if self.name in entry.transitions:
                # print("found a circular ref")
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
                # print(entry.transitions)
                pass

    # replace a transition with a link
    def link_internal(self,token,start,end):
        linked = False
        for index in range(0,len(self)):
            if token in self.table[index].transitions:
                linked = True
                # remove the transition and get the endpoint
                dest = self.table[index].transitions.pop(token)

                # link transition to the location where we are inserting
                self.table[index].add(None,start)   # add new location

                # link into endpoint
                self.table[end].epsilons.update(dest)
        if not linked:
            # print("Failed to link {} in {}".format(token,self.name))
            return False
        return True

    def insert(self,other):
        other_start = len(self)
        other.shift_table(other_start)
        self.extend(other)
        return other_start

    def link(self,other,start_id,dest_id=None):
        # offset table entries
        self.shift_table(len(other))

        # link this NFA's accept states to the dest state
        if dest_id != None:
            for state in self.accept:
                self.table[state].add(None,dest_id)  # link into other
                self.table[state].tags.remove(ACCEPT_T) # unmark accept states

        # link transition to the location where we are inserting
        other.table[start_id].epsilons.add(len(other))   # add new location

        other.extend(self)    # extend the result NFA with the linked copy

    # garbage collect this NFA
    # returns a new NFA with no unreachable states
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
        start_super = self._collect_reachable([self.start])
        to_add = set([start_super])

        while len(to_add) != 0:
            new_add = set()
            for superstate in to_add:
                # print(superstate)
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
        # caller may have metadata to attach based superstate composition
        return sorted_table,table_ids


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
    grammar.follow()
    follows = dict()
    for nt in grammar.nonterminals:
        nonterm = grammar.nonterminals[nt]
        follows[nonterm.symbol] = set([follow for follow in nonterm.follow])
    return follows

def main():
    with open("cow.json","r") as src:
        g = Grammar.create(json.loads(src.read()))

    print("NULLABLES:")
    pp.pprint(nullable(g))

    print("STARTS:")
    pp.pprint(first(g))

    print("FOLLOWS:")
    pp.pprint(follow(g))

    print("PARSING:")
    parser = ParsingAutomaton("PARSER",g).build()

    with open("../code/test.cow","r") as f:
        parser.parse(f.read().strip().split())

    # print(base.gc())

def parse_error(reason):
    print("Error: {}".format(reason))
    exit(1)

if __name__ == '__main__':
    main()