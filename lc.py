"""
Lambda Calculus Beta Recuction Tool
===================================

:Author: Jack Rosenthal (jack@rosenth.al)
"""

import re
import readline
import argparse


class ControlToken:
    """
    Base class for all control tokens.
    """
    def __repr__(self):
        return self.__class__.__name__


T = {k: type(k, (ControlToken, ), dict(ControlToken.__dict__))
     for k in ("(", ")", "λ", ".", "=")}


class Shorthand(str):
    def lrepr(self):
        return '{{{}}}'.format(self)


class Term:
    pass


class Variable(Term):
    id_counter = 0

    def __init__(self, name):
        self.name = name
        self.id = Variable.id_counter
        self.bound = False
        Variable.id_counter += 1

    def lrepr(self):
        return self.name

    def bind(self, var):
        if self.name == var.name:
            if self.bound:
                raise ValueError('{} is already bound'.format(self.name))
            self.id = var.id
            self.bound = True

    def alpha_eq(self, other, renames={}):
        if not isinstance(other, Variable):
            return False
        lesser, greater = sorted([self.id, other.id])
        return renames.get(lesser) == greater

    def apply(self, vid, t):
        if self.id == vid:
            return t
        return self

    def tree(self, indent=''):
        print("Variable")
        print(indent, "|- name: ", self.name, sep='')
        print(indent, "|- id: ", self.id, sep='')
        print(indent, "`- bound: ", self.bound, sep='')


class Abstraction(Term):
    def __init__(self, var, term, bind=True):
        self.var = var
        if bind:
            term.bind(var)
        self.term = term

    def lrepr(self):
        return 'λ{}.{}'.format(self.var.lrepr(), self.term.lrepr())

    def bind(self, var):
        if self.var.name == var.name:
            return
        self.term.bind(var)

    def alpha_eq(self, other, renames={}):
        if not isinstance(other, Abstraction):
            return False
        lesser, greater = sorted([self.var.id, other.var.id])
        renames = renames.copy()
        renames[lesser] = greater
        return self.term.alpha_eq(other.term, renames)

    def apply(self, vid, t):
        return Abstraction(self.var, self.term.apply(vid, t), bind=False)

    @property
    def bound(self):
        return self.term.bound

    def tree(self, indent=''):
        print("Abstraction")
        print(indent, "|- var:", end=' ', sep='')
        self.var.tree(indent + '|       ')
        print(indent, "`- term:", end=' ', sep='')
        self.term.tree(indent + '         ')


class Application(Term):
    def __init__(self, m, n):
        self.m = m
        self.n = n

    def lrepr(self):
        mr = self.m.lrepr()
        nr = self.n.lrepr()
        if isinstance(self.m, Abstraction):
            mr = '({})'.format(mr)
        if not isinstance(self.n, Variable):
            nr = '({})'.format(nr)
        return '{}{}'.format(mr, nr)

    def bind(self, var):
        self.m.bind(var)
        self.n.bind(var)

    def alpha_eq(self, other, renames={}):
        if not isinstance(other, Application):
            return False
        return (self.m.alpha_eq(other.m, renames)
                and self.n.alpha_eq(other.n, renames))

    def apply(self, vid, t):
        return Application(self.m.apply(vid, t), self.n.apply(vid, t))

    @property
    def bound(self):
        return self.m.bound and self.n.bound

    def tree(self, indent=''):
        print("Application")
        print(indent, "|- m:", end=' ', sep='')
        self.m.tree(indent + "|     ")
        print(indent, "`- n:", end=' ', sep='')
        self.n.tree(indent + "      ")


class Definition:
    def __init__(self, name, term):
        self.name = name
        if not term.bound:
            raise SyntaxError("Shorthands may only have fully bound terms")
        self.term = term


tokens_p = re.compile(r'''
    \s*(?:  (?P<control>\(|\)|λ|\.|=)
       |    (?P<shorthand>\{[^}]+\})
       |    (?P<numeral>[0-9]+)
       |    (?P<variable>[^0-9{}λ.])
       )\s*''', re.VERBOSE)


def tokenize(code):
    last_end = 0
    for m in tokens_p.finditer(code):
        if m.start() != last_end:
            raise SyntaxError("malformed input")
        if m.group('control'):
            yield T[m.group('control')]()
        elif m.group('shorthand'):
            yield Shorthand(m.group('shorthand')[1:-1].upper())
        elif m.group('numeral'):
            yield Shorthand(m.group('numeral'))
        else:
            yield Variable(m.group('variable'))
        last_end = m.end()
    if last_end != len(code):
        raise SyntaxError("malformed input")


def match(stack, types):
    if len(stack) < len(types):
        return False
    for elem, t in zip(reversed(stack), reversed(types)):
        if not isinstance(elem, t):
            return False
    return True


def parse(tokens, shorthands={}):
    digits_p = re.compile(r'\d+')
    stack = []
    lookahead = next(tokens)
    while True:
        if match(stack, (T['('], Term, T[')'])):
            # Reduce by Term -> ( Term )
            _, t, _ = (stack.pop() for _ in range(3))
            stack.append(t)
        elif match(stack, (Term, Term)):
            # Reduce by Application -> Term Term
            n, m = (stack.pop() for _ in range(2))
            stack.append(Application(m, n))
        elif (match(stack, (T['λ'], Variable, T['.'], Term))
              and (lookahead is None
                   or isinstance(lookahead, T[')']))):
            # Reduce by Abstraction -> λ Variable . Term
            t, _, x, _ = (stack.pop() for _ in range(4))
            stack.append(Abstraction(x, t))
        elif (match(stack, (Shorthand, T['='], Term))
              and lookahead is None):
            # Reduce by Definition -> Shorthand = Term
            t, _, s = (stack.pop() for _ in range(3))
            if digits_p.match(s):
                raise SyntaxError('Church numerals cannot be redefined')
            stack.append(Definition(s, t))
        elif (match(stack, (Shorthand, ))
              and not isinstance(lookahead, T['='])):
            s = stack.pop()
            if digits_p.match(s):
                stack.append(church_numeral(int(s)))
            elif s in shorthands.keys():
                stack.append(shorthands[s])
            else:
                raise KeyError('undefined shorthand {!r}'.format(s))
        else:
            # Shift
            if lookahead is None:
                break
            try:
                stack.append(lookahead)
                lookahead = next(tokens)
            except StopIteration:
                lookahead = None
    if (len(stack) == 1
        and (isinstance(stack[0], Term)
             or isinstance(stack[0], Definition))):
        return stack.pop()
    raise SyntaxError("incomplete parse")


def church_numeral(n):
    a = Variable('x')
    for _ in range(n):
        a = Application(Variable('f'), a)
    return Abstraction(Variable('f'), Abstraction(Variable('x'), a))


def church_to_int(t):
    if not isinstance(t, Abstraction):
        return
    f = t.var
    t = t.term
    if not isinstance(t, Abstraction):
        return
    x = t.var
    i = 0
    t = t.term
    while isinstance(t, Application):
        if not isinstance(t.m, Variable):
            return
        if t.m.id != f.id:
            return
        i += 1
        t = t.n
    if not isinstance(t, Variable) or t.id != x.id:
        return
    return i


def recursive_reduction(term):
    while isinstance(term, Application):
        if isinstance(term.m, Abstraction):
            term = term.m.term.apply(term.m.var.id, term.n)
            yield term
        elif isinstance(term.m, Application):
            for t in recursive_reduction(term.m):
                term = Application(t, term.n)
                yield term
                break
            else:
                break
        elif isinstance(term.n, Application):
            for t in recursive_reduction(term.n):
                term = Application(term.m, t)
                yield term
                break
            else:
                break
        else:
            break
    if isinstance(term, Abstraction):
        for t in recursive_reduction(term.term):
            yield Abstraction(term.var, t, bind=False)


def show_reduction(term, shorthands={}, ast=False):
    print("INPUT", term.lrepr())
    if ast:
        term.tree()

    for term in recursive_reduction(term):
        print("β ==>", term.lrepr())
        if ast:
            term.tree()

    print()
    found_one = False
    church = church_to_int(term)
    if church is not None:
        print("Potential shorthand representations:")
        print("-> As Church numeral {}".format(church))
        found_one = True
    for k, v in shorthands.items():
        if term.alpha_eq(v):
            if not found_one:
                print("Potential shorthand representations:")
            print("-> As {}".format(k.lrepr()))
            found_one = True
    if not found_one:
        print("No known shorthand representations.")


def repl():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--show-ast',
        action='store_true',
        default=False,
        help='Show a big abstract syntax tree with stuff that gets printed')
    args = parser.parse_args()

    shorthands = {}

    # preload default shorthands
    defaults = [
        "{succ}=λn.λf.λx.f(nfx)",
        "{add}=λm.λn.(m{succ}n)",
        "{mult}=λm.λn.(m({add}n)0)",
        "{true}=λx.λy.x",
        "{false}=λx.λy.y",
        "{and}=λp.λq.pqp",
        "{or}=λp.λq.ppq",
        "{not}=λp.p{false}{true}",
        "{if}=λp.λa.λb.pab",
        "{cons}=λx.λy.λf.fxy",
        "{car}=λc.c{true}",
        "{cdr}=λc.c{false}",
        "{nil}=λx.{true}",
        "{pred}=λn.λf.λx.n(λg.λh.h(gf))(λu.x)(λu.u)",
        "{sub}=λm.λn.n{pred}m",
        "{zero?}=λn.n(λx.{false}){true}",
        "{nil?}=λp.p(λx.λy.{false})",
        "{lte?}=λm.λn.{zero?}({sub}mn)"]

    for d in defaults:
        defn = parse(tokenize(d), shorthands)
        shorthands[defn.name] = defn.term

    def completer(text, state):
        readline.insert_text('λ')

    readline.parse_and_bind(r'"\\": complete')
    readline.parse_and_bind(r'tab: complete')
    readline.set_completer(completer)

    while True:
        try:
            iput = input("λ> ")
        except KeyboardInterrupt:
            print()
            continue
        except EOFError:
            return
        else:
            try:
                if iput.strip():
                    term = parse(tokenize(iput), shorthands)
                    if isinstance(term, Definition):
                        shorthands[term.name] = term.term
                        continue
                    if not term.bound:
                        print("Input is not fully bound")
                        continue
                    show_reduction(term, shorthands, ast=args.show_ast)
            except Exception as e:
                print("{}: {}".format(e.__class__.__name__, e))


if __name__ == '__main__':
    repl()
