#!/usr/bin/env python
# -*- coding: ISO-8859-1 -*-
#
#
# Copyright (C) 2004 André Wobst <wobsta@users.sourceforge.net>
#
# This file is part of PyX (http://pyx.sourceforge.net/).
#
# PyX is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# PyX is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with PyX; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

import Numeric, LinearAlgebra


class scalar:
    # represents a scalar variable or constant

    def __init__(self, value=None, varname="unnamed_scalar"):
        self.value = None
        if value is not None:
            self.set(value)
        self.varname = varname

    def addend(self):
        return addend([self], None)

    def term(self):
        return term([self.addend()])

    def __add__(self, other):
        return self.term() + other

    __radd__ = __add__

    def __sub__(self, other):
        return self.term() - other

    def __rsub__(self, other):
        return -self.term() + other

    def __neg__(self):
        return -self.addend()

    def __mul__(self, other):
        return self.addend()*other

    __rmul__ = __mul__

    def __div__(self, other):
        return self.addend()/other

    def is_set(self):
        return self.value is not None

    def set(self, value):
        if self.is_set():
            raise RuntimeError("variable already defined")
        try:
            self.value = float(value)
        except:
            raise RuntimeError("float expected")

    def get(self):
        if not self.is_set():
            raise RuntimeError("variable not yet defined")
        return self.value

    def __str__(self):
        if self.is_set():
            return "%s{=%s}" % (self.varname, self.value)
        else:
            return self.varname

    def __float__(self):
        return self.get()


class vector:
    # represents a vector, i.e. a list of scalars

    def __init__(self, dimension_or_values, varname="unnamed_vector"):
        try:
            varname + ""
        except TypeError:
            raise RuntimeError("a vectors varname should be a string (you probably wanted to write vector([x, y]) instead of vector(x, y))")
        try:
            # values
            self.scalars = [scalar(value=value, varname="%s[%i]" % (varname, i))
                            for i, value in enumerate(dimension_or_values)]
        except (TypeError, AttributeError):
            # dimension
            self.scalars = [scalar(varname="%s[%i]" % (varname, i))
                            for i in range(dimension_or_values)]
        self.varname = varname

    def __len__(self):
        return len(self.scalars)

    def __getitem__(self, i):
        return self.scalars[i]

    def __getattr__(self, attr):
        if attr == "x":
            return self[0]
        if attr == "y":
            return self[1]
        if attr == "z":
            return self[2]
        else:
            raise AttributeError(attr)

    def addend(self):
        return addend([], self)

    def term(self):
        return term([self.addend()])

    def __add__(self, other):
        return self.term() + other

    __radd__ = __add__

    def __sub__(self, other):
        return self.term() - other

    def __rsub__(self, other):
        return -self.term() + other

    def __neg__(self):
        return -self.addend()

    def __mul__(self, other):
        return self.addend()*other

    __rmul__ = __mul__

    def __div__(self, other):
        return self.addend()/other

    def __str__(self):
        return "%s{=(%s)}" % (self.varname, ", ".join([str(scalar) for scalar in self.scalars]))


class addend:
    # represents an addend of a term, i.e. a list of scalars and
    # optionally a vector (for a vector term) otherwise the vector
    # is None

    def __init__(self, scalars, vector):
        # self.vector might be None for a scalar addend
        self.scalars = scalars
        self.vector = vector

    def __len__(self):
        return len(self.vector)

    def __getitem__(self, i):
        return addend(self.scalars + [self.vector[i]], None)

    def addend(self):
        return self

    def term(self):
        return term([self.addend()])

    def is_linear(self):
        assert self.vector is None
        return len([scalar for scalar in self.scalars if not scalar.is_set()]) < 2

    def prefactor(self):
        assert self.is_linear()
        prefactor = 1
        for scalar_set in [scalar for scalar in self.scalars if scalar.is_set()]:
            prefactor *= scalar_set.get()
        return prefactor

    def variable(self):
        assert self.is_linear()
        try:
            variable, = [scalar for scalar in self.scalars if not scalar.is_set()]
        except ValueError:
            return None
        else:
            return variable

    def __add__(self, other):
        return self.term() + other

    __radd__ = __add__

    def __sub__(self, other):
        return self.term() - other

    def __rsub__(self, other):
        return -self.term() + other

    def __neg__(self):
        return addend([scalar(-1)] + self.scalars, self.vector)

    def __mul__(self, other):
        try:
            a = other.addend()
        except (TypeError, AttributeError):
            try:
                t = other.term()
            except (TypeError, AttributeError):
                return self*scalar(other)
            else:
                return term([self*a for a in t.addends])
        else:
            if a.vector is not None:
                if self.vector is not None:
                    if len(self.vector) != len(a.vector):
                        raise RuntimeError("vector length mismatch in scalar product")
                    return term([addend(self.scalars + a.scalars + [x*y], None)
                                 for x, y in zip(self.vector, a.vector)])
                else:
                    return addend(self.scalars + a.scalars, a.vector)
            else:
                return addend(self.scalars + a.scalars, self.vector)

    __rmul__ = __mul__

    def __div__(self, other):
        return addend([scalar(1/other)] + self.scalars, self.vector)

    def __str__(self):
        scalarstring = " * ".join([str(scalar) for scalar in self.scalars])
        if self.vector is None:
            return scalarstring
        else:
            if len(scalarstring):
                scalarstring += " * "
            return scalarstring + str(self.vector)


class term:
    # represents a term, i.e. a list of addends

    def __init__(self, addends):
        assert len(addends)
        try:
            self.length = len(addends[0])
        except (TypeError, AttributeError):
            for addend in addends[1:]:
                try:
                    len(addend)
                except (TypeError, AttributeError):
                    pass
                else:
                    raise RuntimeError("vector addend in scalar term")
            self.length = None
        else:
            for addend in addends[1:]:
                try:
                    l = len(addend)
                except (TypeError, AttributeError):
                    raise RuntimeError("scalar addend in vector term")
                if l != self.length:
                    raise RuntimeError("vector length mismatch in term constructor")
        self.addends = addends

    def __len__(self):
        if self.length is None:
            raise AttributeError("scalar term")
        else:
            return self.length

    def __getitem__(self, i):
        return term([addend[i] for addend in self.addends])

    def term(self):
        return self

    def is_linear(self):
        is_linear = 1
        for addend in self.addends:
            is_linear = is_linear and addend.is_linear()
        return is_linear

    def __add__(self, other):
        try:
            t = other.term()
        except:
            return self + scalar(other)
        else:
            return term(self.addends + t.addends)

    __radd__ = __add__

    def __neg__(self):
        return term([-addend for addend in self.addends])

    def __sub__(self, other):
        return -other+self

    def __rsub__(self, other):
        return -self+other

    def __mul__(self, other):
        return term([addend*other for addend in self.addends])

    __rmul__ = __mul__

    def __div__(self, other):
        return term([addend/other for addend in self.addends])

    def __str__(self):
        return "  +  ".join([str(addend) for addend in self.addends])


class Solver:
    # linear equation solver

    def __init__(self):
        self.eqs = [] # scalar equations not yet solved (a equation is a term to be zero here)

    def eq(self, lhs, rhs=None):
        if rhs is None:
            eq = lhs
        else:
            eq = lhs - rhs
        eq = eq.term()
        try:
            # is it a vector equation?
            neqs = len(eq)
        except (TypeError, AttributeError):
            self.add(eq)
        else:
            for i in range(neqs):
                self.add(eq[i])

    def add(self, equation):
        # the equation is just a term which should be zero
        self.eqs.append(equation)

        # try to solve some combinations of equations
        while 1:
            for eqs in self.combine(self.eqs):
                if self.solve(eqs):
                    break # restart for loop
            else:
                break # quit while loop

    def combine(self, eqs):
        # create combinations of linear equations
        if not len(eqs):
            yield []
        else:
            for x in self.combine(eqs[1:]):
                yield x
            if eqs[0].is_linear():
                for x in self.combine(eqs[1:]):
                    yield [eqs[0]] + x

    def solve(self, eqs):
        # try to solve a set of linear equations
        l = len(eqs)
        if l:
            vars = []
            for eq in eqs:
                for addend in eq.addends:
                    var = addend.variable()
                    if var is not None and var not in vars:
                        vars.append(var)
            if len(vars) == l:
                a = Numeric.zeros((l, l))
                b = Numeric.zeros((l, ))
                for i, eq in enumerate(eqs):
                    for addend in eq.addends:
                        var = addend.variable()
                        if var is not None:
                            a[i, vars.index(var)] += addend.prefactor()
                        else:
                            b[i] -= addend.prefactor()
                for i, value in enumerate(LinearAlgebra.solve_linear_equations(a, b)):
                    vars[i].set(value)
                for eq in eqs:
                    i, = [i for i, selfeq in enumerate(self.eqs) if selfeq == eq]
                    del self.eqs[i]
                return 1
            elif len(vars) < l:
                raise RuntimeError("equations are overdetermined")
        return 0

solver = Solver()


if __name__ == "__main__":

    x = vector(2, "x")
    y = vector(2, "y")
    z = vector(2, "z")

    solver.eq(4*x + y, 2*x - y + vector([4, 0])) # => x + y = (2, 0)
    solver.eq(x[0] - y[0], z[1])
    solver.eq(x[1] - y[1], z[0])
    solver.eq(vector([5, 0]), z)

    print x
    print y
    print z
