#!/usr/bin/env python
# -*- coding: ISO-8859-1 -*-
#
#
# Copyright (C) 2002-2004 Jörg Lehmann <joergl@users.sourceforge.net>
# Copyright (C) 2002-2006 André Wobst <wobsta@users.sourceforge.net>
# Copyright (C) 2005 Michael Schindler <m-schindler@users.sourceforge.net>
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

import math, types

def sign(x):
    return (x >= 0) and 1 or -1

try:
    import Numeric, LinearAlgebra
    _has_numeric = 1
except:
    _has_numeric = 0

def evrealtrisym(d, e):
    """returns eigenvalues of a tridiagonal real symmetric matrix

    d are the diagonal elements and e are the subdiagonal elements.
    len(d) == len(e) + 1; d and e are destroyed
    """
    n = len(d)
    assert len(d) == len(e) + 1
    e = e + [0.0]
    for l in range(n):
        for iter in range(30):
            for m in range(l, n-1):
                dd = abs(d[m]) + abs(d[m+1])
                if abs(e[m]) + dd == dd:
                    break
            else:
                m = n-1
            if m == l:
                break
            g = (d[l+1]-d[l]) / (2.0*e[l])
            r = math.hypot(g, 1.0)
            if g >= 0:
                g = d[m]-d[l]+e[l]/(g+abs(r))
            else:
                g = d[m]-d[l]+e[l]/(g-abs(r))
            s = c = 1.0
            p = 0.0
            for i in range(m, l, -1):
                f = s*e[i-1]
                b = c*e[i-1]
                e[i] = r = math.hypot(f, g)
                if r == 0.0:
                    d[i] -= p
                    e[m] = 0.0
                    break
                s = f/r
                c = g/r
                g = d[i]-p
                r = (d[i-1]-g)*s + 2.0*c*b
                p = s*r
                d[i] = g+p
                g = c*r-b
            else:
                d[l] -= p
                e[l] = g
                e[m] = 0.0
        else:
            raise RuntimeError("Too many iterations in evrealtrisym")
    return d

def realsymtotrisym(a):
    """creates a real tridiagonal matrix out of a real symmetric matrix

    Eigenvalues are not altered by the transformation; a is the matrix, i.e. a
    list of lists but only the diagonal and off-diagonal elements left of the
    diagonal are accessed (the other values don't need to be provided and the
    lists might be shortend); a is destroyed
    """
    n = len(a)
    d = [None] * n
    e = [None] * (n-1)
    x = [None] * (n-1)
    for i in range(n-1, 0, -1):
        l = i
        h = scale = 0.0
        if l > 1:
            for k in range(l):
                scale += abs(a[i][k])
            if scale == 0.0:
                e[i-1] = a[i][l-1]
            else:
                for k in range(l):
                    a[i][k] /= scale
                    h += a[i][k]*a[i][k]
                f = a[i][l-1]
                g = math.sqrt(h)
                if f >= 0:
                    g = -g
                e[i-1] = scale*g
                h -= f*g
                a[i][l-1] = f-g
                f = 0.0
                for j in range(l):
                    g = 0.0
                    for k in range(j+1):
                        g += a[j][k]*a[i][k]
                    for k in range(j+1, l):
                        g += a[k][j]*a[i][k]
                    x[j] = g/h
                    f += x[j]*a[i][j]
                hh = 0.5*f/h
                for j in range(l):
                    f = a[i][j]
                    x[j] = g = x[j]-hh*f
                    for k in range(j+1):
                        a[j][k] -= f*x[k] + g*a[i][k]
        else:
            e[i-1] = a[i][l-1]
        d[i] = h
    for i in range(n):
        d[i] = a[i][i]
    return d, e

def evrealsym(a):
    """returns eigenvalues of a real symmetric matrix

    a is a real symmetric matrix, i.e. a list of lists but only the diagonal
    and off-diagonal elements below the diagonal are accessed (other values are
    not accessed, i.e. the lists might be shortend).
    """
    # make a copy and ensure floats
    a = [[float(x) for x in row] for row in a]
    return evrealtrisym(*realsymtotrisym(a))

def balancerealsquare(a, radix=2):
    """modify a general real square matrix to become balanced

    This routine replaces the general real square matrix a by a balanced matrix
    with identical eigenvalues. A symmetric matrix is already balanced and is
    unaffected by this procedure. The parameter radix should be the machine's
    floating-point radix to prevent any numerical inaccuracies to be introduced
    by this method.
    """
    n = len(a)
    radix2 = radix*radix
    last = 0
    while not last:
        last = 1
        for i in range(n):
            r = c = 0.0
            for j in range(n):
                if j+1 != i+1:
                    c += abs(a[j][i])
                    r += abs(a[i][j])
            if c != 0 and r != 0:
                g = r/radix
                f = 1.0
                s = c+r
                while c < g:
                    f *= radix
                    c *= radix2
                g = r*radix
                while c > g:
                    f /= radix
                    c /= radix2
                if (c+r)/f < 0.95*s:
                    last = 0
                    g = 1.0/f
                    for j in range(n):
                        a[i][j] *= g
                    for j in range(n):
                        a[j][i] *= f

def hessrealsquare(a):
    """modify a general real square matrix to the upper hessenberg form

    This routine replaces the general real square matrix a by a hessenberg
    formed matrix with identical eigenvalues.
    """
    n = len(a)
    for m in range(1, n-1):
        x = 0.0
        i = m
        for j in range(m, n):
            if (abs(a[j][m-1]) > abs(x)):
                x = a[j][m-1]
                i = j
        if i != m:
            for j in range(m-1, n):
                a[i][j], a[m][j] = a[m][j], a[i][j]
            for j in range(n):
                a[j][i], a[j][m] = a[j][m], a[j][i]
        if x:
            for i in range(m+1, n):
                y = a[i][m-1]
                if y:
                    y /= x
                    a[i][m-1] = y
                    for j in range(m, n):
                        a[i][j] -= y*a[m][j]
                    for j in range(n):
                        a[j][m] += y*a[j][i]
    for i in range(2, n):
        for j in range(i-1):
            a[i][j] = 0

def evhessrealsquare(a, realonly=0):
    """returns eigenvalues of a real square matrix in upper hessenberg form

    a is a real square matrix in upper hessenberg form. a is destroyed.
    The return value is a list containing a mixture of floats and complex
    values.
    """
    n = len(a)
    e = []

    anorm = 0.0
    for i in range(n):
        for j in range(n):
            anorm += abs(a[i][j])
    t = 0.0
    while n > 0:
        its = 0
        first = 1
        while first or l < n-2:
            first = 0
            for l in range(n-1, 0, -1):
                s = abs(a[l-1][l-1]) + abs(a[l][l])
                if s:
                    s = anorm
                if abs(a[l][l-1]) + s == s:
                    break
            else:
                l = 0
            x = a[n-1][n-1]
            if l == n-1:
                e.append(x+t)
                n -= 1
            else:
                y = a[n-2][n-2]
                w = a[n-1][n-2]*a[n-2][n-1]
                if l == n-2:
                    p = 0.5*(y-x)
                    q = p*p+w
                    z = math.sqrt(abs(q))
                    x += t
                    if q >= 0.0:
                        if p >= 0:
                            z = p + abs(z)
                        else:
                            z = p - abs(z)
                        e.append(x+z)
                        if z:
                            e.append(x-w/z)
                        else:
                            e.append(x+z)
                    elif not realonly:
                        e.append(x+p - z*1J)
                        e.append(x+p + z*1J)
                    n -= 2
                else:
                    if its == 30:
                        raise RuntimeError("Too many iterations in evhessrealsquare")
                    if its == 10 or its == 20:
                        t += x
                        for i in range(n):
                            a[i][i] -= x
                        s = abs(a[n-1][n-2]) + abs(a[n-2][n-3])
                        y = x = 0.75*s
                        w = -0.4375*s*s
                    its += 1
                    for m in range(n-3, l-1, -1):
                        z = a[m][m]
                        r = x-z
                        s = y-z
                        p = (r*s-w)/a[m+1][m] + a[m][m+1]
                        q = a[m+1][m+1]-z-r-s
                        r = a[m+2][m+1]
                        s = abs(p)+abs(q)+abs(r)
                        p /= s
                        q /= s
                        r /= s
                        if m == l:
                            break
                        u = abs(a[m][m-1])*(abs(q)+abs(r))
                        v = abs(p) * (abs(a[m-1][m-1]) + abs(z) + abs(a[m+1][m+1]))
                        if u + v == v:
                            break
                    for i in range(m+2, n):
                        a[i][i-2] = 0.0
                        if i != m+2:
                            a[i][i-3]=0.0
                    for k in range(m, n-1):
                        if k != m:
                            p = a[k][k-1]
                            q = a[k+1][k-1]
                            r = 0.0
                            if k != n-2:
                                r = a[k+2][k-1]
                            x = abs(p) + abs(q) + abs(r)
                            if x:
                                p /= x
                                q /= x
                                r /= x
                        if p >= 0:
                            s = math.sqrt(p*p+q*q+r*r)
                        else:
                            s = -math.sqrt(p*p+q*q+r*r)
                        if s:
                            if k == m:
                                if l != m:
                                    a[k][k-1] = -a[k][k-1]
                            else:
                                a[k][k-1] = -s*x
                            p += s
                            x = p/s
                            y = q/s
                            z = r/s
                            q /= p
                            r /= p
                            for j in range(k, n):
                                p = a[k][j]+q*a[k+1][j]
                                if k != n-2:
                                    p += r*a[k+2][j]
                                    a[k+2][j] -= p*z
                                a[k+1][j] -= p*y
                                a[k][j] -= p*x
                            mmin = min(n-1, k+3)
                            for i in range(l, mmin+1):
                                p = x*a[i][k] + y*a[i][k+1]
                                if k != n-2:
                                    p += z*a[i][k+2]
                                    a[i][k+2] -= p*r
                                a[i][k+1] -= p*q
                                a[i][k] -= p
                            else:
                                i = mmin + 1
    return e

def evrealsquare(a, copy=1, realonly=0):
    """returns eigenvalues of a real square matrix

    a is a real square matrix, i.e. a list of lists. The return value is a list
    containing a mixture of floats and complex values.
    """
    if copy:
        # make a copy and ensure floats
        a = [[float(x) for x in row] for row in a]
    balancerealsquare(a)
    hessrealsquare(a)
    return evhessrealsquare(a, realonly=realonly)

def realpolyroots(coeffs, epsilon=1e-5):
    """returns the roots of a polynom with given coefficients

    polynomial with coefficients given in coeffs:
      0 = \sum_i x^i coeffs[i]
    The solution is found via an equivalent eigenvalue problem
    """
    if not coeffs:
        return []
    try:
        f = -1.0 / coeffs[-1]
    except ZeroDivisionError:
        return realpolyroots(coeffs[:-1])
    else:
        n = len(coeffs) - 1
        if _has_numeric:
            a = Numeric.zeros((n, n), Numeric.Float)
            for i in range(n-1):
                a[i+1][i] = 1
            for i in range(n):
                a[0][i] = f*coeffs[n-1-i]
            roots = []
            for root in LinearAlgebra.eigenvalues(a):
                if type(root) == types.ComplexType:
                    if not root.imag:
                        roots.append(root.real)
                else:
                    roots.append(root)
            return roots
        else:
            a = [[0.0 for i in range(n)] for j in range(n)]
            for i in range(n-1):
                a[i+1][i] = 1.0
            for i in range(n):
                a[0][i] = f*coeffs[n-1-i]
            return evrealsquare(a, copy=0, realonly=1)
