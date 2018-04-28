import re
import readline


class CtrlTok:
    class DefineShorthand: pass
    class LParen: pass
    class RParen: pass
    class Lambda: pass
    class Dot: pass

    stringmap = {
        '(': LParen,
        ')': RParen,
        'λ': Lambda,
        '.': Dot,
        '=': DefineShorthand}


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
        lesser, greater = sorted(self.var.id, other.var.id)
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
        if isinstance(self.n, Abstraction):
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

    def beta(self):
        if isinstance(self.m, Application):
            return Application(self.m.beta(), self.n)
        return self.m.term.apply(self.m.var.id, self.n)

    def apply(self, vid, t):
        return Application(self.m.apply(vid, t), self.n.apply(vid, t))

    @property
    def bound(self):
        return self.m.bound and self.n.bound

    def tree(self, indent=''):
        print("Application")
        print(indent , "|- m:", end=' ', sep='')
        self.m.tree(indent + "|     ")
        print(indent, "`- n:", end=' ', sep='')
        self.n.tree(indent + "      ")


tokens_p = re.compile(r'''
    \s*(?:  (?P<control>\(|\)|λ|\.|=)
       |    (?P<shorthand>\{[^}]+\})
       |    (?P<variable>[^{}λ.])
       )\s*''', re.VERBOSE)


def tokenize(code):
    last_end = 0
    for m in tokens_p.finditer(code):
        if m.start() != last_end:
            raise SyntaxError("malformed input")
        if m.group('control'):
            yield CtrlTok.stringmap[m.group('control')]()
        elif m.group('shorthand'):
            yield Shorthand(m.group('shorthand')[1:-1])
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


def parse(tokens):
    stack = []
    lookahead = next(tokens)
    while True:
        if match(stack, (CtrlTok.LParen, Term, CtrlTok.RParen)):
            # Reduce by Term -> ( Term )
            _, t, _ = (stack.pop() for _ in range(3))
            stack.append(t)
        elif match(stack, (Term, Term)):
            # Reduce by Application -> Term Term
            n, m = (stack.pop() for _ in range(2))
            stack.append(Application(m, n))
        elif (match(stack, (CtrlTok.Lambda, Variable, CtrlTok.Dot, Term))
              and (lookahead is None
                   or isinstance(lookahead, CtrlTok.RParen))):
            # Reduce by Abstraction -> λ Variable . Term
            t, _, x, _ = (stack.pop() for _ in range(4))
            stack.append(Abstraction(x, t))
        else:
            # Shift
            if lookahead is None:
                break
            try:
                stack.append(lookahead)
                lookahead = next(tokens)
            except StopIteration:
                lookahead = None
    if len(stack) == 1:
        return stack.pop()
    raise SyntaxError("incomplete parse")


def show_reduction(term):
    print("INPUT", term.lrepr())
    while isinstance(term, Application):
        term = term.beta()
        print("β ==>", term.lrepr())


def repl():

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
                    term = parse(tokenize(iput))
                    if not term.bound:
                        print("Input is not fully bound")
                        continue
                    show_reduction(term)
            except Exception as e:
                print("{}: {}".format(e.__class__.__name__, e))


if __name__ == '__main__':
    repl()
