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

import types, sets
import Numeric, LinearAlgebra


valuetypes = (types.IntType, types.LongType, types.FloatType)


class scalar:
    # this class represents a scalar variable

    def __init__(self, varname="(no variable name provided)"):
        self.id = id(self) # compare the id to check for the same variable
                           # (the __eq__ method is used to define "equalities")
        self.varname = varname
        self.value = None

    def term(self):
        return term([1], [self], 0)

    def __add__(self, other):
        return term([1], [self], 0) + other

    __radd__ = __add__

    def __neg__(self):
        return term([-1], [self], 0)

    def __sub__(self, other):
        return term([1], [self], 0) - other

    def __rsub__(self, other):
        return term([-1], [self], 0) + other

    def __mul__(self, other):
        return term([other], [self], 0)

    __rmul__ = __mul__

    def __div__(self, other):
        return term([1/other], [self], 0)

    def __eq__(self, other):
        return term([1], [self], 0) == other

    def is_set(self):
        return self.value is not None

    def set(self, value):
        if self.is_set():
            raise RuntimeError("variable already defined")
        self.value = value

    def get(self):
        if not self.is_set():
            raise RuntimeError("variable not yet defined")
        return self.value

    def __str__(self):
        if self.is_set():
            return "%s[=%s]" % (self.varname, self.value)
        else:
            return self.varname

    def __float__(self):
        return self.get()


class vector(scalar):

    def __init__(self, dimension, varname="(no variable name provided)"):
        scalar.__init__(self, varname=varname)
        del self.value # disallow is_set, set, get
        self.scalars = [scalar(varname="%s%i" % (varname, i)) for i in range(dimension)]

    def __getitem__(self, i):
        return self.scalars[i]

    def __str__(self):
        return "%s[=(%s)]" % (self.varname, ",".join([str(scalar) for scalar in self.scalars]))


class point:

    def __init__(self, *values):
        self.values = values

    def term(self):
        return term([], [], self)

    def __getitem__(self, i):
        return self.values[i]

    def __add__(self, other):
        if other is 0: # XXX: is 0 ?!
            # the default constant in a term is zero, but it should be interpreted as a point(0, ...) as well
            return self
        else:
            try:
                # other might be a point and we should return a point
                # (this is the typical case for term.const in a vector equation)
                return point(*[x + y for x, y in zip(self.values, other.values)])
            except AttributeError:
                # otherwise its likely, that the other item is a term and we
                # should return a term
                return self.term() + other

    __radd__ = __add__

    def __neg__(self):
        return point(*[-value for value in self.values])

    def __sub__(self, other):
        return -other+self

    def __rsub__(self, other):
        return -self+other

    def __mul__(self, other):
        return point(*[other*value for value in self.values])

    __rmul__ = __mul__

    def __div__(self, other):
        return point(*[value/other for value in self.values])


class term:
    # this class represents the linear term:
    # sum([p*v.value for p, v in zip(self.prefactors, self.vars]) + self.const

    def __init__(self, prefactors, vars, const):
        assert len(prefactors) == len(vars)
        self.id = id(self) # compare the id to check for the same term
                           # (the __eq__ method is used to define "equalities")
        self.prefactors = prefactors
        self.vars = vars
        self.const = const

    def term(self):
        return self

    def __add__(self, other):
        try:
            other = other.term()
        except:
            other = term([], [], other)
        vars = self.vars[:]
        prefactors = self.prefactors[:]
        vids = [v.id for v in vars] # already existing variable ids
        for p, v in zip(other.prefactors, other.vars):
            try:
                # try to modify prefactor for existing variables
                prefactors[vids.index(v.id)] += p
            except ValueError:
                # or add the variable
                vars.append(v)
                prefactors.append(p)
        return term(prefactors, vars, self.const + other.const)

    __radd__ = __add__

    def __neg__(self):
        return term([-p for p in self.prefactors], self.vars, -self.const)

    def __sub__(self, other):
        return -other+self

    def __rsub__(self, other):
        return -self+other

    def __mul__(self, other):
        return term([p*other for p in self.prefactors], self.vars, self.const*other)

    __rmul__ = __mul__

    def __div__(self, other):
        return term([p/other for p in self.prefactors], self.vars, self.const/other)

    def __eq__(self, other):
        eq = self - other
        if not len(eq.vars):
            raise RuntimeError("equation without variables")
        try:
            # is it a vector equation?
            neqs = len(eq.vars[0].scalars)
        except AttributeError:
            for v in eq.vars[1:]:
                try:
                    v.scalars
                except AttributeError:
                    pass
                else:
                    raise RuntimeError("mixed scalar/vector equation")
            solver.add(eq)
        else:
            for v in eq.vars[1:]:
                if len(v.scalars) != neqs:
                    raise RuntimeError("vectors of different dimension")
            if eq.const is 0: # XXX: is 0 ?!
                eq.const = point(*([0]*neqs))
            elif len(eq.const.values) != neqs:
                raise RuntimeError("wrong dimension of constant")
            for i in range(neqs):
                solver.add(term(eq.prefactors, [var[i] for var in eq.vars], eq.const[i]))

    def __str__(self):
        return "+".join(["%s*%s" % pv for pv in zip(self.prefactors, self.vars)]) + "+" + str(self.const)


class Solver:
    # linear equation solver

    def __init__(self):
        self.eqs = [] # equations still to be taken into account

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
        # create combinations of equations
        if not len(eqs):
            yield []
        else:
            for x in self.combine(eqs[1:]):
                yield x
                yield [eqs[0]] + x

    def solve(self, eqs):
        # try to solve a set of equations
        l = len(eqs)
        if l:
            vids = []
            for eq in eqs:
                vids.extend([v.id for v in eq.vars if v.id not in vids and not v.is_set()])
            if len(vids) == l:
                a = Numeric.zeros((l, l))
                b = Numeric.zeros((l, ))
                index = {}
                for i, vid in enumerate(vids):
                    index[vid] = i
                vars = {}
                for i, eq in enumerate(eqs):
                    for p, v in zip(eq.prefactors, eq.vars):
                        if v.is_set():
                            b[i] -= p*v.value
                        else:
                            a[i, index[v.id]] += p
                            vars[index[v.id]] = v
                    b[i] -= eq.const
                for i, value in enumerate(LinearAlgebra.solve_linear_equations(a, b)):
                    vars[i].value = value
                for eq in eqs:
                    i, = [i for i, selfeq in enumerate(self.eqs) if selfeq.id == eq.id]
                    del self.eqs[i]
                return 1
            elif len(vids) < l:
                raise RuntimeError("equations are overdetermined")
        return 0

solver = Solver()


if __name__ == "__main__":

    x = vector(2, "x")
    y = vector(2, "y")
    z = vector(2, "z")

    4*x + y == 2*x - y + point(4, 0) # => x + y = (2, 0)
    x[0] - y[0] == z[1]
    x[1] - y[1] == z[0]
    point(5, 0) == z

    print x, y, z


