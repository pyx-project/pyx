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

    def __sub__(self, other):
        return term([1], [self], 0) - other

    def __rsub__(self, other):
        return term([-1], [self], 0) + other

    def __neg__(self):
        return term([-1], [self], 0)

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
            return str(self.value)
        else:
            return self.varname

    def __float__(self):
        return self.get()


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
        vids = [v.id for v in vars]
        for p, v in zip(other.prefactors, other.vars):
            try:
                prefactors[vids.index(v.id)] += p
            except ValueError:
                vars.append(v)
                prefactors.append(p)
        return term(prefactors, vars, self.const + other.const)

    __radd__ = __add__

    def __sub__(self, other):
        return self + (-other)

    def __neg__(self):
        return term([-p for p in self.prefactors], self.vars, -self.const)

    def __rsub__(self, other):
        return -self+other

    def __mul__(self, other):
        return term([p*other for p in self.prefactors], self.vars, self.const*other)

    __rmul__ = __mul__

    def __div__(self, other):
        return term([p/other for p in self.prefactors], self.vars, self.const/other)

    def __eq__(self, other):
        solver.add(self-other)

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
            else:
                assert len(vids) > l
        return 0

solver = Solver()


if __name__ == "__main__":

    x = scalar("x")
    y = scalar("y")
    z = scalar("z")

    x + y == 2*x - y + 3
    x - y == z
    5 == z

    print "x=%s" % x
    print "y=%s" % y
    print "z=%s" % z


