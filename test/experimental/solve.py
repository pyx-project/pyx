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


def sum(list):
    # we can assume len(list) != 0 here (and do not start from the scalar 0)
    sum = list[0]
    for item in list[1:]:
        sum += item
    return sum

def product(list):
    # we can assume len(list) != 0 here (and do not start from the scalar 1)
    product = list[0]
    for item in list[1:]:
        product *= item
    return product


class scalar:
    # represents a scalar variable or constant

    def __init__(self, value=None, name="unnamed_scalar"):
        self._scalar = None
        if value is not None:
            self.set(value)
        self.name = name

    def scalar(self):
        return self

    def addend(self):
        return addend([self])

    def polynom(self):
        return self.addend().polynom()

    def __neg__(self):
        return -self.addend()

    def __add__(self, other):
        return self.polynom() + other

    __radd__ = __add__

    def __sub__(self, other):
        return self.polynom() - other

    def __rsub__(self, other):
        return -self.polynom() + other

    def __mul__(self, other):
        return self.addend()*other

    __rmul__ = __mul__

    def __div__(self, other):
        return self.addend()/other

    def is_set(self):
        return self._scalar is not None

    def set(self, value):
        if self.is_set():
            raise RuntimeError("scalar already defined")
        try:
            self._scalar = float(value)
        except:
            raise RuntimeError("float expected")

    def get(self):
        if not self.is_set():
            raise RuntimeError("scalar not yet defined")
        return self._scalar

    def __float__(self):
        return self.get()

    def __str__(self):
        if self.is_set():
            return "%s{=%s}" % (self.name, self._scalar)
        else:
            return self.name


class addend:
    # represents a addend, i.e. list of scalars to be multiplied by each other

    def __init__(self, scalars):
        self._scalars = [scalar.scalar() for scalar in scalars]
        if not len(self._scalars):
            raise RuntimeError("empty scalars not allowed")

    def addend(self):
        return self

    def polynom(self):
        return polynom([self])

    def __neg__(self):
        return addend([scalar(-1)] + self._scalars)

    def __add__(self, other):
        return self.polynom() + other

    __radd__ = __add__

    def __sub__(self, other):
        return self.polynom() - other

    def __rsub__(self, other):
        return -self.polynom() + other

    def __mul__(self, other):
        try:
            other = other.addend()
        except (TypeError, AttributeError):
            try:
                other = scalar(other)
            except RuntimeError:
                return other * self
            else:
                return addend(self._scalars + [other])
        else:
            return addend(self._scalars + other._scalars)

    __rmul__ = __mul__

    def __div__(self, other):
        return addend([scalar(1/other)] + self._scalars)

    def __float__(self):
        return product([float(scalar) for scalar in self._scalars])

    def is_linear(self):
        return len([scalar for scalar in self._scalars if not scalar.is_set()]) < 2

    def prefactor(self):
        assert self.is_linear()
        setscalars = [scalar for scalar in self._scalars if scalar.is_set()]
        if len(setscalars):
            return float(addend(setscalars))
        else:
            return 1.0

    def variable(self):
        assert self.is_linear()
        unsetscalars = [scalar for scalar in self._scalars if not scalar.is_set()]
        if len(unsetscalars):
            assert len(unsetscalars) == 1
            return unsetscalars[0]
        else:
            return None

    def __str__(self):
        return " * ".join([str(scalar) for scalar in self._scalars])


class polynom:
    # represents a polynom, i.e. a list of addends to be summed up

    def __init__(self, polynom):
        self._addends = [addend.addend() for addend in polynom]
        if not len(self._addends):
            raise RuntimeError("empty polynom not allowed")

    def polynom(self):
        return self

    def __neg__(self):
        return polynom([-addend for addend in self._addends])

    def __add__(self, other):
        try:
            other = other.polynom()
        except (TypeError, AttributeError):
            other = scalar(other).polynom()
        return polynom(self._addends + other._addends)

    __radd__ = __add__

    def __sub__(self, other):
        return -other + self

    def __rsub__(self, other):
        return -self + other

    def __mul__(self, other):
        return sum([addend*other for addend in self._addends])

    __rmul__ = __mul__

    def __div__(self, other):
        return polynom([addend/other for addend in self._addends])

    def __float__(self):
        return sum([float(addend) for addend in self._addends])

    def is_linear(self):
        is_linear = 1
        for addend in self._addends:
            is_linear = is_linear and addend.is_linear()
        return is_linear

    def __str__(self):
        return "  +  ".join([str(addend) for addend in self._addends])

    def solve(self, solver):
        solver.addequation(self)


class vector:
    # represents a vector, i.e. a list of terms

    def __init__(self, dimension_or_values, name="unnamed_vector"):
        try:
            name + ""
        except TypeError:
            raise RuntimeError("a vectors name should be a string (you probably wanted to write vector([x, y]) instead of vector(x, y))")
        try:
            for value in dimension_or_values:
                pass
        except:
            # dimension
            self._items = [scalar(name="%s[%i]" % (name, i))
                           for i in range(dimension_or_values)]
        else:
            # values
            self._items = []
            for value in dimension_or_values:
                try:
                    value.polynom()
                except (TypeError, AttributeError):
                    self._items.append(scalar(value=value, name="%s[%i]" % (name, len(self._items))))
                else:
                    self._items.append(value)
        if not len(self._items):
            raise RuntimeError("empty vector not allowed")
        self.name = name

    def __len__(self):
        return len(self._items)

    def __getitem__(self, i):
        return self._items[i]

    def __getattr__(self, attr):
        if attr == "x":
            return self[0]
        if attr == "y":
            return self[1]
        if attr == "z":
            return self[2]
        else:
            raise AttributeError(attr)

    def vector(self):
        return self

    def __neg__(self):
        return vector([-item for item in self._items])

    def __add__(self, other):
        other = other.vector()
        if len(self) != len(other):
            raise RuntimeError("vector length mismatch in add")
        return vector([selfitem + otheritem for selfitem, otheritem in zip(self._items, other._items)])

    __radd__ = __add__

    def __sub__(self, other):
        return -other + self

    def __rsub__(self, other):
        return -self + other

    def __mul__(self, other):
        try:
            other = scalar(other)
        except:
            pass
        try:
            other = other.vector()
        except (TypeError, AttributeError):
            try:
                other = other.polynom()
            except (TypeError, AttributeError):
                # inverse matrix multiplication ?
                return other.__rmul__(self)
            else:
                return vector([item*other for item in self._items])
        else:
            # scalar product
            if len(self) != len(other):
                raise RuntimeError("vector length mismatch in scalar product")
            return sum([selfitem*otheritem for selfitem, otheritem in zip(self._items, other._items)])

    __rmul__ = __mul__

    def __div__(self, other):
        return vector([item/other for item in self._items])

    def __str__(self):
        return "%s{=(%s)}" % (self.name, ", ".join([str(item) for item in self._items]))

    def solve(self, solver):
        for item in self._items:
            solver.addequation(item)


class matrix:
    # represents a matrix, i.e. a 2d list of terms

    def __init__(self, dimensions_or_values, name="unnamed_matrix"):
        try:
            name + ""
        except TypeError:
            raise RuntimeError("a matrix name should be a string (you probably wanted to write matrix([x, y]) instead of matrix(x, y))")
        try:
            for row in dimensions_or_values:
                for col in row:
                    pass
        except:
            # dimension
            self._numberofrows, self._numberofcols = [int(x) for x in dimensions_or_values]
            self._rows = [[scalar(name="%s[%i, %i]" % (name, row, col))
                           for col in range(self._numberofcols)]
                          for row in range(self._numberofrows)]
        else:
            # values
            self._rows = []
            self._numberofcols = None
            for row in dimensions_or_values:
                _cols = []
                for col in row:
                    try:
                        col.polynom()
                    except (TypeError, AttributeError):
                        _cols.append(scalar(value=col, name="%s[%i, %i]" % (name, len(self._rows), len(_cols))))
                    else:
                        _cols.append(col)
                self._rows.append(_cols)
                if self._numberofcols is None:
                    self._numberofcols = len(_cols)
                elif self._numberofcols != len(_cols):
                    raise RuntimeError("column length mismatch")
            self._numberofrows = len(self._rows)
        if not self._numberofrows or not self._numberofcols:
            raise RuntimeError("empty matrix not allowed")
        self.name = name

    def __getitem__(self, (row, col)):
        return self._rows[row][col]

    def matrix(self):
        return self

    def __neg__(self):
        return matrix([[-col for col in row] for row in self._rows])

    def __add__(self, other):
        other = other.matrix()
        if self._numberofrows != other._numberofrows or self._numberofcols != other._numberofcols:
            raise RuntimeError("matrix geometry mismatch in add")
        return matrix([[selfcol + othercol
                        for selfcol, othercol in zip(selfrow, otherrow)]
                       for selfrow, otherrow in zip(self._rows, other._rows)])

    __radd__ = __add__

    def __sub__(self, other):
        return -other + self

    def __rsub__(self, other):
        return -self + other

    def __mul__(self, other):
        try:
            other = other.matrix()
        except (TypeError, AttributeError):
            try:
                other = other.vector()
            except (TypeError, AttributeError):
                return matrix([[col*other for col in row] for row in self._rows])
            else:
                if self._numberofcols != len(other):
                    raise RuntimeError("size mismatch in matrix vector product")
                return vector([sum([col*otheritem
                                    for col, otheritem in zip(row, other)])
                               for row in self._rows])
        else:
            if self._numberofcols != other._numberofrows:
                raise RuntimeError("size mismatch in matrix product")
            return matrix([[sum([self._rows[row][i]*other._rows[i][col]
                                 for i in range(self._numberofcols)])
                            for col in range(other._numberofcols)]
                           for row in range(self._numberofrows)])

    def __rmul__(self, other):
        try:
            other = other.vector()
        except (TypeError, AttributeError):
            return matrix([[other*col for col in row] for row in self._rows])
        else:
            if self._numberofrows != len(other):
                raise RuntimeError("size mismatch in matrix vector product")
            return vector([sum([other[i]*self._rows[i][col]
                                for i in range(self._numberofrows)])
                           for col in range(self._numberofcols)])

    def __div__(self, other):
        return matrix([[col/other for col in row] for row in self._rows])

    def __str__(self):
        return "%s{=(%s)}" % (self.name, ", ".join(["(" + ", ".join([str(col) for col in row]) + ")" for row in self._rows]))

    def solve(self, solver):
        for row in self._rows:
            for col in row:
                solver.addequation(col)


class Solver:
    # linear equation solver

    def __init__(self):
        self.eqs = [] # scalar equations not yet solved (a equation is a polynom to be zero)

    def eq(self, lhs, rhs=None):
        if rhs is None:
            eq = lhs
        else:
            eq = lhs - rhs
        eq.solve(self)

    def addequation(self, equation):
        # the equation is just a polynom which should be zero
        self.eqs.append(equation.polynom())

        # try to solve some combinations of linear equations
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
                for addend in eq._addends:
                    var = addend.variable()
                    if var is not None and var not in vars:
                        vars.append(var)
            if len(vars) == l:
                a = Numeric.zeros((l, l), Numeric.Float)
                b = Numeric.zeros((l, ), Numeric.Float)
                for i, eq in enumerate(eqs):
                    for addend in eq._addends:
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

    # x = vector(2, "x")
    # y = vector(2, "y")
    # z = vector(2, "z")

    # solver.eq(4*x + y, 2*x - y + vector([4, 0])) # => x + y = (2, 0)
    # solver.eq(x[0] - y[0], z[1])
    # solver.eq(x[1] - y[1], z[0])
    # solver.eq(vector([5, 0]), z)

    # print x
    # print y
    # print z

    A = matrix([2, 2])
    solver.eq(vector([1, 1]), A * vector([0, 1]))
    solver.eq(vector([0, 2]), A * vector([1, 0]))

    I = matrix([2, 2])
    solver.eq(vector([0, 1]), I * vector([0, 1]))
    solver.eq(vector([1, 0]), I * vector([1, 0]))

    B = matrix([2, 2])
    solver.eq(I, A*B)

    print A
    print B


