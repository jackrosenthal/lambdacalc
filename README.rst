``lc``: The Lambda Calculus Beta Reducer
========================================

This tool helps you β-reduce terms in the λ-calculus by providing you with a
REPL::

   λ> (λc.c(λx.λy.x))((λx.λy.λf.fxy)(λf.λx.f(fx))(λf.λx.f(f(fx))))
   INPUT (λc.c(λx.λy.x))((λx.λy.λf.fxy)(λf.λx.f(fx))(λf.λx.f(f(fx))))
   β ==> (λx.λy.λf.fxy)(λf.λx.f(fx))(λf.λx.f(f(fx)))(λx.λy.x)
   β ==> (λy.λf.f(λf.λx.f(fx))y)(λf.λx.f(f(fx)))(λx.λy.x)
   β ==> (λf.f(λf.λx.f(fx))(λf.λx.f(f(fx))))(λx.λy.x)
   β ==> (λx.λy.x)(λf.λx.f(fx))(λf.λx.f(f(fx)))
   β ==> (λy.λf.λx.f(fx))(λf.λx.f(f(fx)))
   β ==> λf.λx.f(fx)

   Potential shorthand representations:
   -> As Church numeral 2

Input
-----

Notice the pretty unicode ``λ`` in the input: this REPL uses Readline to input
a ``λ`` when you type backslash (``\``).

Shorthands
----------

   You can start any 'Monty Python' routine and people finish it for you.
   Everyone knows it like shorthand.

   -- Robin Williams


Notice above the input was converted to its corresponding shorthand Church
numeral at the end. This interpreter has the notion of shorthand notations:

1. Shorthands are written in braces (``{}``) and are *case insensitive*.

2. Church numerals, as well as many other common shorthands, are predefined for
   you.

3. Braces can be omitted on church numerals, as digits are not allowed to be
   used as variables.

4. Use ``=`` operator to define a shorthand.

::

    λ> {ABC}=λf.λx.x
    λ> {ABC}
    INPUT λf.λx.x

    Potential shorthand representations:
    -> As Church numeral 0
    -> As {FALSE}
    -> As {ABC}
    λ> {IF}{FALSE}1{ABC}
    INPUT (λp.λa.λb.pab)(λx.λy.y)(λf.λx.fx)(λf.λx.x)
    β ==> (λa.λb.(λx.λy.y)ab)(λf.λx.fx)(λf.λx.x)
    β ==> (λb.(λx.λy.y)(λf.λx.fx)b)(λf.λx.x)
    β ==> (λx.λy.y)(λf.λx.fx)(λf.λx.x)
    β ==> (λy.y)(λf.λx.x)
    β ==> λf.λx.x

    Potential shorthand representations:
    -> As Church numeral 0
    -> As {FALSE}
    -> As {ABC}

Builtin Shorthands
~~~~~~~~~~~~~~~~~~

Besides a countably infinite number of Church numerals, the following
shorthands come builtin to the interpreter::

   {succ}=λn.λf.λx.f(nfx)
   {add}=λm.λn.(m{succ}n)
   {mult}=λm.λn.(m({add}n)0)
   {true}=λx.λy.x
   {false}=λx.λy.y
   {and}=λp.λq.pqp
   {or}=λp.λq.ppq
   {not}=λp.p{false}{true}
   {if}=λp.λa.λb.pab
   {cons}=λx.λy.λf.fxy
   {car}=λc.c{true}
   {cdr}=λc.c{false}
   {nil}=λx.{true}
   {pred}=λn.λf.λx.n(λg.λh.h(gf))(λu.x)(λu.u)
   {sub}=λm.λn.n{pred}m
   {zero?}=λn.n(λx.{false}){true}
   {nil?}=λp.p(λx.λy.{false})
   {lte?}=λm.λn.{zero?}({sub}mn)

Bugs
----

   None.  Mutts have fleas, not bugs.

   -- Mutt Manual Page

* ``{pred}`` (and, consequently, ``{sub}``) appear to have some sort of issue.

* When variables conflict as a result of application, they will display as the
  same variable, but the interpreter will still treat them as separate
  variables. What needs to be done is some sort of detection mechanism when
  this happens, and an automatic α-rename of the variable.

If you solve either of these, a PR is much appreciated!
