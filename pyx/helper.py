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


class nodefault:
    """not-set keyword argument marker

    This class is used to mark keyword arguments to be not set by the user.
    """
    pass


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

