# this code is really a mess ...

import sys
from Numeric import *
from RandomArray import *
from LinearAlgebra import *
from FFT import *


sqrt2 = math.sqrt(2)


def norm(v):
    return math.sqrt(reduce(lambda x, y: x+y*y, v, 0))

def blochvector(l, k):
    assert k >= 0 and k <= l/2
    v = cos(2*math.pi/l*(k)*arange(l))
    return v/norm(v)

def localvector(l, pos):
    v = zeros(l)
    v[pos] = 1
    return v/norm(v)

def local2vector(l, pos1, pos2):
    v = zeros(l)
    v[pos1] = 1
    v[pos2] = 1
    return v/norm(v)



def diag_anderson(l, w):

    """diagonalize the anderson model"""

    seed(x=1705, y=1111)
    pot=w*random(l)-0.5*w
    ham = zeros((l, l), Float)
    for i in xrange(l):
        ham[i, i] = pot[i]
        ham[i, (i+1)%l] = -1
        ham[i, (i-1)%l] = -1
    evalues, evectors = eigenvectors(ham)
    sorter = argsort(evalues)
    return take(evalues, sorter), take(evectors, sorter)



def diag_harper_full(l, lam):

    """diagonalize the harper model by full diagonalization"""

    def fibs(tonumber):
        result = [1, 1]
        while result[-1] < tonumber:
            result.append(result[-2]+result[-1])
        return result

    l2, ltest = fibs(l)[-2:]
    if ltest != l: raise ValueError("l isn't a fibonacci number")

    pot=lam*cos((2*pi*l2*arange(l))/l)
    ham = zeros((l, l), Float)
    for i in xrange(l):
        ham[i, i] = pot[i]
        ham[i, (i+1)%l] = 1
        ham[i, (i-1)%l] = 1
    evalues, evectors = eigenvectors(ham)
    sorter = argsort(evalues)
    return take(evalues, sorter), take(evectors, sorter)



def diag_harper(l, lam):

    """diagonalize the harper model by diagonalizing the symmetric and antisymmetic parts"""

    def fibs(tonumber):
        result = [1, 1]
        while result[-1] < tonumber:
            result.append(result[-2]+result[-1])
        return result

    def createsymm(dest, source):
        l = len(dest)
        if l % 2:
            dest[0] = source[0]
            for i in xrange(1, (l+1)/2):
                dest[i] = dest[l-i] = source[i] / sqrt2
        else:
            dest[0] = source[0]
            dest[l/2] = source[l/2]
            for i in xrange(1, l/2):
                dest[i] = dest[l-i] = source[i] / sqrt2

    def createasymm(dest, source):
        l = len(dest)
        if l % 2:
            dest[0] = 0
            for i in xrange(1, (l+1)/2):
                dest[i] = source[i-1] / sqrt2
                dest[l-i] = -source[i-1] / sqrt2
        else:
            dest[0] = dest[l/2] = 0
            for i in xrange(1, l/2):
                dest[i] = -source[i-1] / sqrt2
                dest[l-i] = source[i-1] / sqrt2

    l2, ltest = fibs(l)[-2:]
    if ltest != l: raise ValueError("l isn't a fibonacci number")

    # symmetric and antisymmetric diagonalization
    if l%2:
        # odd
        symmsize = (l-1)/2 + 1
        pot = lam*cos((2*pi*l2*arange(symmsize))/l)
        pot[symmsize - 1] += 1
        symmham = zeros((symmsize, symmsize), Float)
        for i in xrange(symmsize):
            symmham[i, i] = pot[i]
            if i > 1:
                symmham[i, i-1] = symmham[i-1, i] = 1
            elif i:
                symmham[i, i-1] = symmham[i-1, i] = sqrt2
    else:
        # even
        symmsize = l/2 + 1
        pot = lam*cos((2*pi*l2*arange(symmsize))/l)
        symmham = zeros((symmsize, symmsize), Float)
        for i in xrange(symmsize):
            symmham[i, i] = pot[i]
            if i > 1 and i < symmsize - 1:
                symmham[i, i-1] = symmham[i-1, i] = 1
            elif i:
                symmham[i, i-1] = symmham[i-1, i] = sqrt2
    symmevalues, symmevectors = eigenvectors(symmham)

    if l%2:
        # odd
        asymmsize = (l-1)/2
        pot = lam*cos((2*pi*l2*(arange(asymmsize)+1))/l)
        pot[asymmsize-1] -= 1
        asymmham = zeros((asymmsize, asymmsize), Float)
        for i in xrange(asymmsize):
            asymmham[i, i] = pot[i]
            if i:
                asymmham[i, i-1] = asymmham[i-1, i] = 1
    else:
        # even
        asymmsize = l/2 - 1
        pot = lam*cos((2*pi*l2*(arange(asymmsize)+1))/l)
        asymmham = zeros((asymmsize, asymmsize), Float)
        for i in xrange(asymmsize):
            asymmham[i, i] = pot[i]
            if i:
                asymmham[i, i-1] = asymmham[i-1, i] = 1
    asymmevalues, asymmevectors = eigenvectors(asymmham)

    # build complete solution
    symmsort = argsort(symmevalues)
    asymmsort = argsort(asymmevalues)
    j = k = 0
    evalues = zeros((l,), Float)
    evectors = zeros((l, l), Float)
    for i in xrange(l):
        if j != symmsize and (k == asymmsize or
                              symmevalues[symmsort[j]] < asymmevalues[asymmsort[k]]):
            evalues[i] = symmevalues[symmsort[j]]
            createsymm(evectors[i], symmevectors[symmsort[j]])
            j += 1
        else:
            evalues[i] = asymmevalues[asymmsort[k]]
            createasymm(evectors[i], asymmevectors[asymmsort[k]])
            k += 1
    return evalues, evectors



def test_harper(l, lam):

    """compare diag_harper and diag_harper_full"""

    res1 = diag_harper(l, lam)
    res2 = diag_harper_full(l, lam)
    for x1, x2 in zip(res1[0], res2[0]):
        assert math.fabs(x1-x2) < 1e-8, "eigenvalues differ"
    for v1, v2 in zip(res1[1], res2[1]):
        sum = 0
        for x1, x2 in zip(v1, v2):
            sum += x1 * x2
        if sum > 0:
            for x1, x2 in zip(v1, v2):
                assert math.fabs(x1-x2) < 1e-8, "eigenvectors differ\n%s\n%s" % (v1, v2)
        else:
            for x1, x2 in zip(v1, v2):
                assert math.fabs(x1+x2) < 1e-8, "eigenvectors differ\n%s\n%s" % (v1, -v2)

# test_harper(13, 5)



def wigner_slow(vector):

    """create wigner function of a state (direct way)"""

    l = len(vector)
    wig = zeros((l, l), Float)

    # wigner function (direct way)
    for x0loop in xrange(l):
        x0 = x0loop
        for k0loop in xrange(l):
            if l%2:
                k0 = (k0loop-0.5*l+0.5)*2*pi/l
            else:
                k0 = (k0loop-0.5*l+1)*2*pi/l
            sum = 0j
            for yloop in xrange(l):
                y = yloop - l/2 + 1 - l%2
                v = lambda x: vector[(x+10*l)%l]
                if y%2:
                    v1 = 0.5*(v(x0-(y-1)/2) + v(x0-(y+1)/2))
                    v2 = 0.5*(v(x0+(y-1)/2) + v(x0+(y+1)/2))
                #    v1 = 0
                #    v2 = 0
                else:
                    v1 = v(x0-y/2)
                    v2 = v(x0+y/2)
                sum += v1 * v2 * exp(1j*k0*y)
            assert abs(sum.imag) < 1e-10, "imaginary part should be zero"
            wig[x0loop, k0loop] = sum.real

    return wig



def wigner(vector):

    """create wigner function of a state (fft)"""

    l = len(vector)
    wig = zeros((l, l), Float)

    fftarray = zeros(l, Float)
    fftresult = zeros(l, Complex)
    wig = zeros((l, l), Float)
    for x0loop in xrange(l):
        x0 = x0loop
        for yloop in xrange(l):
            y = yloop - l/2 + 1 - l%2
            v = lambda x: vector[(x+10*l)%l]
            if y%2:
                v1 = 0.5*(v(x0-(y-1)/2) + v(x0-(y+1)/2))
                v2 = 0.5*(v(x0+(y-1)/2) + v(x0+(y+1)/2))
            #    v1 = 0
            #    v2 = 0
            else:
                v1 = v(x0-y/2)
                v2 = v(x0+y/2)
            fftarray[(y+10*l)%l] = v1 * v2
        fftresult = real_fft(fftarray)
        for k0loop in xrange(l):
            if l%2:
                index = int(abs(k0loop-0.5*l+0.5))
            else:
                index = int(abs(k0loop-0.5*l+1))
            wig[x0loop, k0loop] = fftresult[index].real

    return wig



def test_wigner(vector):

    """compare wigner_slow and wigner"""

    res1 = wigner_slow(vector)
    res2 = wigner(vector)
    for v1, v2 in zip(res1, res2):
        for x1, x2 in zip(v1, v2):
            assert math.fabs(x1-x2) < 1e-8, "wigner function differs\n%s\n%s" % (res1, res2)

# test_wigner(diag_anderson(10, 1)[1][5])
# test_wigner(diag_anderson(11, 1)[1][5])


def husimi_from_wigner(wig):

    """calculate the husimi function out of the wigner function"""

    l = len(wig)
    sigma = sqrt(l/pi/4)

    hus = zeros((l, l), Float)
    for x1 in xrange(l):
        for k1 in xrange(l):
            sys.stderr.write("wigner -> husimi (very slow) ...%6.2f%%\r" % ((100.0*(x1*l+k1))/l/l))
            hus[x1, k1] = 0
            for x2 in xrange(l):
                for k2 in xrange(l):
                    dx = x1-x2
                    if dx < -l/2: dx += l
                    if dx > l/2: dx -= l
                    dk = k1-k2
                    if dk < -l/2: dk += l
                    if dk > l/2: dk -= l
                    dk *= 2*pi/l
                    hus[x1, k1] += 2.0/l/l * wig[x2, k2] * exp(-0.5*dx*dx/sigma/sigma-2*sigma*sigma*dk*dk)
    sys.stderr.write("wigner -> husimi (very slow) ... done.   \n")

    return hus



def husimi_slow(vector):

    l = len(vector)
    hus = zeros((l, l), Float)
    phases = zeros((l, l), Float)
    sigma=sqrt(l/pi/4)
    factor=1/sqrt(sqrt(2*pi)*sigma*l)

    for x0loop in xrange(l):
        x0 = x0loop
        for k0loop in xrange(l):
            if l%2:
                k0 = (k0loop-0.5*l+0.5)*2*pi/l
            else:
                k0 = (k0loop-0.5*l+1)*2*pi/l
            sum = 0j
            for x in xrange(l):
                phase = exp(1j*k0*x)
                sum += vector[x] * factor * exp(-(x-x0-l)*(x-x0-l)/(4*sigma*sigma)) * phase
                sum += vector[x] * factor * exp(-(x-x0  )*(x-x0  )/(4*sigma*sigma)) * phase
                sum += vector[x] * factor * exp(-(x-x0+l)*(x-x0+l)/(4*sigma*sigma)) * phase
            hus[x0loop, k0loop] = abs(sum)*abs(sum)
            phases[x0loop, k0loop] = math.atan2(sum.imag, sum.real)

    return hus, phases



def husimi(vector):

    l = len(vector)
    hus = zeros((l, l), Float)
    sigma=sqrt(l/pi/4)
    factor=1/sqrt(sqrt(2*pi)*sigma*l)

    fftarray = zeros(l, Complex)
    fftresult = zeros(l, Complex)
    heights = zeros((l, l), Float)
    phases = zeros((l, l), Float)
    for x0loop in xrange(l):
        x0 = x0loop
        for xloop in xrange(l):
            x = xloop
            while (x-x0 < -0.5*l): x += l
            while (x-x0 > 0.5*l): x -=l
            fftarray[xloop] = vector[xloop] * factor * exp(-(x-x0)*(x-x0)/(4*sigma*sigma))
        #fftresult = real_fft(fftarray)
        fftresult = fft(fftarray)
        for k0loop in xrange(l):
            if l%2:
                index = (int(k0loop-0.5*l+0.5) + 10*l)%l
                #index = int(abs(k0loop-0.5*l+0.5))
            else:
                raise
                index = int(abs(k0loop-0.5*l+1))
            heights[x0loop, k0loop] = abs(fftresult[index])*abs(fftresult[index])
            phases[x0loop, k0loop] = math.atan2(fftresult[index].imag, fftresult[index].real)
            # if 2*x0loop > l: phases[x0loop, k0loop] = -phases[x0loop, k0loop] + math.pi
            # if 2*k0loop > l: phases[x0loop, k0loop] = -phases[x0loop, k0loop]

    return heights, phases



def test_husimi(vector):

    """compare husimi_slow and husimi"""

    res1 = husimi_slow(vector)
    res2 = husimi(vector)
    for v1, v2 in zip(res1, res2):
        for x1, x2 in zip(v1, v2):
            assert math.fabs(x1-x2) < 1e-8, "husimi function differs\n%s\n%s" % (res1, res2)

# test_husimi(diag_anderson(10, 1)[1][5])
# test_husimi(diag_anderson(11, 1)[1][5])

l=101
values, vectors = diag_anderson(l, 0.5)
vector = vectors[24]
heights, phases = husimi(vector)

f = open("example.dat", "w")
for x in range(l):
    for y in range(l):
        f.write("%i %i %+20.15e %+20.15e\n" % (x, y, heights[x, y], phases[x, y]))
