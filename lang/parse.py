#!/usr/bin/env python2.7
"""
    Proper CFG parser
"""
from __future__ import print_function
import sys
import pprint as pp
import json

TERMINALS_KEY = "terminals"
GENERICS_KEY  = "generics"
RULES_KEY     = "rules"
START_KEY     = "start"
META_START_KEY = "_META_START_"

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
        return Grammar(nonterminals,rules,start)

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