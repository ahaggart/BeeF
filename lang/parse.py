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

# lazily evaluated set nesting framework, for recursively building token sets
# with interdependecnies
class SuperSet:
    def __init__(self,symbol,subsets=[]):
        self.symbol = symbol
        self.subsets = []
        for subset in subsets:
            self.add(subset)

    def __iter__(self,pending=set()): # recursively generate this set's elements
        pending.add(self.symbol)
        # print(class(self))
        for subset in self.subsets:
            if subset.__class__.__name__ != "SuperSet": # pull everything from base sets
                for item in subset:
                    yield item
            elif subset.symbol not in pending:
                for item in subset.__iter__(pending):   # recusively resolve
                    yield item

    def add(self,subset):
        if type(subset) != SuperSet or subset.symbol != self.symbol:
            self.subsets.append(subset)


class Grammar:
    def __init__(self,nonterminals,rules,start):
        self.start          = start
        self.nonterminals   = dict([(nont.symbol,nont) for nont in nonterminals])
#        self.terminals      = terminals
        self.rules          = dict([(rule.symbol,rule) for rule in rules])
        self.start          = start

        if not self.start.symbol in self.nonterminals:
            parse_error("Invalid start variable: {}".format(self.start))

    @staticmethod
    def create(source):
        # TODO: do the class packing in the classes themselves?
        terminals   = set(Terminal(term) for term in source[TERMINALS_KEY])
        generics    = set(source[GENERICS_KEY])
        full_syms = set(source[TERMINALS_KEY])
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
                    print("{}: {}".format(subexp.succ.symbol,subexp.succ.first(self.rules)))
                    ss.add(subexp.succ.first(self.rules))
                    if subexp.succ.nullable(self.rules):
                        if rulename != subexp.token.symbol:
                            print([symbol.token.symbol for symbol in subexp.succ])
                            print("added {} as follow subset of {}".format(rulename,ss.symbol))
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

    def nullable(self,rules,pending=set()):
        if self.is_nullable == None:
            pending.add(self.symbol)
            self.is_nullable = all(self._nullables(rules,pending))
        return self.is_nullable
    def _nullables(self,rules,pending):
        for symbol in self:
            if symbol.symbol not in pending:
                yield symbol.nullable(rules,pending)

    def first(self,rules,pending=set()):
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

    def first(self,rules,pending=set()):
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
        for symbol in str.split(str(source)," "):
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

    def verify(self,chain,rules):
        chain = chain[:] # copy the list
        for symbol in self.symbols:
            if not chain:       # consumed the whole chain, must be valid
                return True
            if not symbol.verify(chain,rules):
                return False
        return False

    def make_NFA(self):
        pass



class Nonterminal:
    def __init__(self,symbol):
        self.symbol = symbol
        self.is_nullable = None
        self.first_symbol = None   
        self.follow = SuperSet(self.symbol)

    def nullable(self,rules,pending=set()):
        if self.is_nullable == None:
            if self.symbol not in rules:
                parse_error("No rule for nonterminal: " + self.symbol)
            pending.add(self.symbol)
            self.is_nullable = any(rules[self.symbol]._nullables(rules,pending))
        return self.is_nullable

    def first(self,rules,pending=set()):
        if self.first_symbol == None:
            if self.symbol not in rules:
                parse_error("No rule for nonterminal: " + self.symbol)
            self.first_symbol = set()
            pending.add(self.symbol)
            self.first_symbol.update(rules[self.symbol].first(rules,pending))
        else:
            print("got cached start tokens for: {}".format(self.symbol))
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

    def first(self,rules,pending=set()):
        first = set()
        for derivation in self.derivations:
            first.update(derivation.first(rules,pending))
        return first        

class Terminal:
    def __init__(self,symbol):
        self.symbol = symbol
    def nullable(self,rules,pending=set()):
        return False
    def first(self,rules,pending=set()):
        return set([self.symbol])

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
    def nullable(self,rules,pending=set()):
        return True
    def first(self,rules,pending=set()):
        return set()
    def subexpressions(self):
        return []
    def verify(self,chain,rules):
        if len(chain) == 0:
            return True
        return False

# parse input token-by-token, using parse table to decide action and state
class ParsingAutomaton:
    def __init__(self):
        pass

class SLRTable:
    def __init__(self):
        pass

class ParsingDFA:
    def __init__(self):
        pass

class ParsingNFA:
    # # require a single accept state
    # def __init__(self):
    #     self.start  = ParsingNFAStart()
    #     self.accept = None

    # def link(self,NFAs):
    #     self.start.link(NFAs)

    # @staticmethod
    # def create(tokens): # create a simple NFA to parse a token list
    #     curr = self.start
    #     for token in tokens:
    #         is_terminal = token.__class__.__name__ != "Nonterminal"
    #         next_state = ParsingNFAState()
    #         curr.add(token.symbol,(next_state,is_terminal))
    #         curr = next_state
    #     self.accept = curr
    #     self.accept.id = 0

    def __init__(self,table=[{}]):
        self.table = table
        self.start = 0 # start state is always id 0

    def add(prev_state,token):
        new_id = len(self.table)
        self.table[prev_state][token] = new_id
        self.table.append({})
        return new_id

    # graft this NFA state into another NFA 
    def graft(other):
        table = [{}]
        self_state_id  = 0
        other_state_id = 0

        self_tokens  = [token for token in  self.table[ self_state_id]]
        other_tokens = [token for token in other.table[other_state_id]]
        for token in (self_tokens|other_tokens):
            pass

    def determine(self): # convert this NFA into a DFA
        table = {}
        start_super = self._collect_reachable([self.start])
        to_add = set(start_super)

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

        # iterate over table and resolve frozen sets into table indices
        sorted_table = [0]*count
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
                dest_sets[token].add(self.table[state].transitions[token])
            dest_sets[token] = self._collect_reachable(dest_sets[token])
        return dest_sets
        
# use tuples of (token,boolean) to denote transitions
# (token,False) denotes a nonterminal transition
class ParsingNFAState:
    def __init__(self):
        self.transitions = {}
        self.epsilons = set()
        self.id = -1
        

    # def add(self,name,state):
    #     self.transitions[name] = state

    # def link(self,NFAs):
    #     removal = set()
    #     for tn in self.transitions:
    #         trans = self.transitions[tn]
    #         trans[1].link(NFAs)
    #         if not trans[1]:
    #             if tn not in NFAs:
    #                 parse_error("No NFA for: {}".format(tn))
    #             removal.add(tn)
    #             # append an epsilon transition into this NFA
    #             self.transitions[EPSILON_T].append(NFAs[tn].start)

    #     for tn in removal:
    #         del self.transition[tn]

    # # # graft this NFA state into another NFA 
    # # def graft(other):

    # # def read(token):
    # #     if token in self.transitions:
    # #         return self.transitions[token]
    # #     parse_error("Parse error after: {}".format(self.name))

# state representing the current expected derivation to parse
# can represent multiple derivations, until a "branch" is reached that rules
# out a potential derivation
class ParsingState:
    def __init__(self,rule,parent):
        # the first tokens we expect to encounter in this state
        # may be terminals or nonterminals
        # if we cannot match any terminals, check each nonterminal first char
        self.rule = [derivation for derivation in rule]

        # track the token chain this state has parsed
        self.chain = []

        # if we encounter a token that should follow the derivation represented
        # by this state, initiate a reduction and pop to the parent state
        self.follow = None
        
        # use stacks of parsing states to trace reductions
        self.parent = parent
        pass

    # read a token, and return the next parsing state to use
    def read(self,token,rules):
        chain.append(token)
        # check if the current derivation step has a rule for expanding it
        if derivation.symbols[step].symbol in rules:
            selection = rule.select(token)
            if selection:
                # we have enough information to select a derivation from the rule
                # ready to construct and use a new parsing state for it
                return ParsingState(selection,self)
            else:
                pass

        # no rule, must be a nonterminal, check if the token matches
        elif derivation.symbols[step].verify(token):
            # match the token and move on to the next step
            pass
        if token in self.follow:
            # initiate a reduction
            pass
        return self

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

def parse_error(reason):
    print("Error: {}".format(reason))
    exit(1)

if __name__ == '__main__':
    main()