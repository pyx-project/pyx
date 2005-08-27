#!/usr/bin/env python
# -*- coding: ISO-8859-1 -*-
#
#
# Copyright (C) 2002-2004 Jörg Lehmann <joergl@users.sourceforge.net>
# Copyright (C) 2002-2004 André Wobst <wobsta@users.sourceforge.net>
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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA


class nodefault: pass


def isstring(arg):
    "arg is string-like (cf. python cookbook 3.2)"
    try: arg + ''
    except: return 0
    return 1


def isnumber(arg):
    "arg is number-like"
    try: arg + 0
    except: return 0
    return 1


def isinteger(arg):
    "arg is integer-like"
    try:
        if type(arg + 0.0) is type(arg):
            return 0
        return 1
    except: return 0


def issequence(arg):
    """arg is sequence-like (e.g. has a len)
       a string is *not* considered to be a sequence"""
    if isstring(arg): return 0
    try: len(arg)
    except: return 0
    return 1


def ensuresequence(arg):
    """return arg or (arg,) depending on the result of issequence,
       None is converted to ()"""
    if isstring(arg): return (arg,)
    if arg is None: return ()
    if issequence(arg): return arg
    return (arg,)


def ensurelist(arg):
    """return list(arg) or [arg] depending on the result of isequence,
       None is converted to []"""
    if isstring(arg): return [arg]
    if arg is None: return []
    if issequence(arg): return list(arg)
    return [arg]

def getitemno(arg, n):
    """get item number n if arg is a sequence (when the sequence
       is not long enough, None is returned), otherweise arg is
       returned"""
    if issequence(arg):
        try: return arg[n]
        except: return None
    else:
        return arg


def issequenceofsequences(arg):
    """check if arg has a sequence or None as it's first entry"""
    return issequence(arg) and len(arg) and (issequence(arg[0]) or arg[0] is None)


def getsequenceno(arg, n):
    """get sequence number n if arg is a sequence of sequences (when
       the sequence is not long enough, None is returned), otherwise
       arg is returned"""
    if issequenceofsequences(arg):
        try: return arg[n]
        except: return None
    else:
        return arg


# XXX fallback for Numeric (eigenvalue computation) to be implemented along
# know algorithms (like from numerical recipes)

import Numeric, LinearAlgebra

def realpolyroots(coeffs, epsilon=1e-5):

    """returns the roots of a polynom with given coefficients

    This helper routine uses the package Numeric to find the roots
    of the polynomial with coefficients given in coeffs:
      0 = \sum_{i=0}^N x^{N-i} coeffs[i]
    The solution is found via an equivalent eigenvalue problem
    """

    try:
        1.0 / coeffs[0]
    except:
        return realpolyroots(coeffs[1:], epsilon=epsilon)
    else:

        N = len(coeffs)
        # build the Matrix of the polynomial problem
        mat = Numeric.zeros((N, N), Numeric.Float)
        for i in range(N-1):
            mat[i+1][i] = 1
        for i in range(N-1):
            mat[0][i] = -coeffs[i+1]/coeffs[0]
        # find the eigenvalues of the matrix (== the zeros of the polynomial)
        zeros = [complex(zero) for zero in LinearAlgebra.eigenvalues(mat)]
        # take only the real zeros
        zeros = [zero.real for zero in zeros if -epsilon < zero.imag < epsilon]

        ## check if the zeros are really zeros!
        #for zero in zeros:
        #    p = 0
        #    for i in range(N):
        #        p += coeffs[i] * zero**(N-i)
        #    if abs(p) > epsilon:
        #        raise Exception("value %f instead of 0" % p)

    return zeros

