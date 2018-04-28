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


class Derivation:
    def __init__(self,symbols):
        self.symbol = None
        self.symbols = symbols
        self.is_nullable = None
        self.first_symbol = None

    @staticmethod
    def create(source,terminals,nonterminals):
        tokens = []
        for symbol in str.split(str(source)," "):
            if symbol in terminals:
                tokens.append(Terminal(symbol))
            elif symbol in nonterminals:
                tokens.append(Nonterminal(symbol))
            else:
                parse_error("Unspecified symbol in rule: {}".format(symbol))
        return Derivation(tokens)

    def nullable(self,rules,pending):
        if self.is_nullable == None:
            self.is_nullable = all(self._nullables(rules,pending))
        return self.is_nullable
    def _nullables(self,rules,pending):
        for symbol in self.symbols:
            if symbol.symbol not in pending:
                yield symbol.nullable(rules,pending)

    def first(self,rules,pending):
        if self.first_symbol == None:
            self.first_symbol = set()
            for symbol in self.symbols:
                if not symbol.nullable(rules,set()):
                    self.first_symbol.update(symbol.first(rules,pending))
                    break
                self.first_symbol.update(symbol.first(rules,pending))
        return self.first_symbol

class Nonterminal:
    def __init__(self,symbol):
        self.symbol = symbol
        self.is_nullable = None
        self.first_symbol = None   

    def nullable(self,rules,pending):
        if self.is_nullable == None:
            if self.symbol not in rules:
                parse_error("No rule for nonterminal: " + self.symbol)
            pending.add(self.symbol)
            self.is_nullable = any(rules[self.symbol]._nullables(rules,pending))
        return self.is_nullable

    def first(self,rules,pending):
        if self.first_symbol == None:
            if self.symbol not in rules:
                parse_error("No rule for nonterminal: " + self.symbol)
            self.first_symbol = set()
            pending.add(self.symbol)
            self.first_symbol.update(rules[self.symbol].first(rules,pending))
        return self.first_symbol
            

class Rule:
    def __init__(self,symbol,derivations):
        self.symbol      = symbol
        self.derivations = derivations
        for derivation in self.derivations:
            derivation.symbol = self.symbol

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
                ders.append(Derivation.create(derivation,terminals,nonterms))
            rules.append(Rule(symbol,ders))
        return rules,nonterms


        

    def _nullables(self,rules,pending):
        if not self.derivations:
            parse_error("Nonterminal has no derivations: "+self.symbols)
        for derivation in self.derivations:
            yield derivation.nullable(rules,pending)

    def first(self,rules,pending):
        first = set()
        for derivation in self.derivations:
            first.update(derivation.first(rules,pending))
        return first

class Terminal:
    def __init__(self,symbol):
        self.symbol = symbol
    def nullable(self,rules,pending):
        return False
    def first(self,rules,pending):
        return set([self.symbol])

class Epsilon: # we might not need this
    def nullable(self,rules,pending):
        return True
    def first(self,rules,pending):
        return set()

# produce a dictionary(variable->terminal) of the first terminals in strings
# generated by each variable
def first(grammar):
    firsts = dict()
    for nt in grammar.nonterminals:
        nonterm = grammar.nonterminals[nt]
        firsts[nonterm.symbol] = nonterm.first(grammar.rules,set()) 
    return firsts

# produce a set(variable) of variables that can generate the empty string
# walk through derivations, using the start variable as entry point
def nullable(grammar):
    nullables = set()
    for nt in grammar.nonterminals:
        nonterm = grammar.nonterminals[nt]
        if nonterm.nullable(grammar.rules,set()):
            nullables.add(nonterm.symbol)
    return nullables
            

def follow(rules):
    pass

def main():
    # start = Nonterminal("start")
    # var1  = Nonterminal("var1")
    # var2  = Nonterminal("var2")

    # epsilon = Epsilon()

    # st = Terminal("s")
    # t1 = Terminal("t1")
    # t2 = Terminal("t2")

    # rstart = Rule(start.symbol,[
    #     Derivation([var1,var2]),
    #     Derivation([st]),
    # ])

    # rvar1 = Rule(var1.symbol,[
    #     Derivation([var2,t2]),
    #     Derivation([t2]),
    # ])

    # rvar2 = Rule(var2.symbol,[
    #     Derivation([var2,t1]),
    #     epsilon,
    # ])

    # g = Grammar(
    #     [start,var1,var2],
    #     [st,t1,t2],
    #     [rstart,rvar1,rvar2],
    #     start
    # )

    with open("cow.json","r") as src:
        g = Grammar.create(json.loads(src.read()))

    print("NULLABLES:")
    pp.pprint(nullable(g))

    print("STARTS:")
    pp.pprint(first(g))

def parse_error(reason):
    print("Error: {}".format(reason))
    exit(1)

if __name__ == '__main__':
    main()