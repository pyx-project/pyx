# this code is really a mess ...

import sys
from Numeric import *
from RandomArray import *
from LinearAlgebra import *
from FFT import *

from pyx import *


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




def plot_grid(grid, filename):

    class griddata(datafile._datafile):

        def __init__(self, grid):
            data = []
            for i in range(len(grid)):
                for j in range(len(grid[i])):
                    if l%2:
                        k = (j-0.5*l+0.5)*2*pi/l
                    else:
                        k = (j-0.5*l+1)*2*pi/l
                    if l%2 or j < len(grid[i]) - 1:
                        data.append([grid[i, j], i+0.5, i+1.5, k-math.pi/l, k+math.pi/l])
                    else:
                        data.append([grid[i, j], i+0.5, i+1.5, -math.pi, -math.pi+math.pi/l])
                        data.append([grid[i, j], i+0.5, i+1.5, math.pi-math.pi/l, math.pi])
            datafile._datafile.__init__(self, ["color", "xmin", "xmax", "kmin", "kmax"], data)

    hd = griddata(grid)

    mypainter = graph.axispainter(baselineattrs=None, zerolineattrs=None, innerticklengths=0, outerticklengths="0.2")

    c = canvas.canvas()
    t = c.insert(tex.tex())
    g = c.insert(graph.graphxy(t, width=10, height=10, x2=None, y2=None, backgroundattrs=canvas.stroked(),
                               x=graph.linaxis(min=0.5, max=len(grid)+0.5, title="$x$",
                                               part=graph.manualpart(ticks=("1", str(len(grid))), texts=("1", "$L$")),
                                               painter=mypainter),
                               y=graph.linaxis(min=-pi, max=pi, divisor=pi, suffix=r"\pi", title="$k$",
                                               part=graph.linpart("1"), painter=mypainter)))
    g.plot(graph.data(hd, color="color", xmin="xmin", xmax="xmax", ymin="kmin", ymax="kmax"),
           graph.rect(color.gradient.ReverseRainbow))
    g.dodata()
    g.finish()
    c.writetofile(filename)




theta = 15 * math.pi/180
phi = -25 * math.pi/180

allscale = 0.07
distance = 150*allscale
gridscale = 1*allscale
zscale = 15*allscale


class gridpoint:

    def __init__(self, x_3d, y_3d, z_3d, x_2d, y_2d, depth, phase):
        self.x_3d = x_3d
        self.y_3d = y_3d
        self.z_3d = z_3d
        self.x_2d = x_2d
        self.y_2d = y_2d
        self.depth = depth
        self.phase = phase

    def __repr__(self):
        return "(%s, %s, %s), (%s, %s), %s, %s " % (self.x_3d, self.y_3d, self.z_3d, self.x_2d, self.y_2d, self.depth, self.phase)

def norm(*list):
    f = 1/math.sqrt(reduce(lambda x, y: x + y*y, list, 0))
    return map(lambda x, f=f: x*f, list)


a = (math.sin(phi), -math.cos(phi), 0)
b = (-math.cos(phi)*math.sin(theta), -math.sin(phi)*math.sin(theta), math.cos(theta))
eye = (distance*math.cos(phi)*math.cos(theta), distance*math.sin(phi)*math.cos(theta), distance*math.sin(theta))

class grid:

    def point_3d(self, x, y, z, phase=0):
        d0 = float(a[0]*b[1]*(z-eye[2]) + a[2]*b[0]*(y-eye[1]) + a[1]*b[2]*(x-eye[0])
                  -a[2]*b[1]*(x-eye[0]) - a[0]*b[2]*(y-eye[1]) - a[1]*b[0]*(z-eye[2]))
        da = (eye[0]*b[1]*(z-eye[2]) + eye[2]*b[0]*(y-eye[1]) + eye[1]*b[2]*(x-eye[0])
             -eye[2]*b[1]*(x-eye[0]) - eye[0]*b[2]*(y-eye[1]) - eye[1]*b[0]*(z-eye[2]))
        db = (a[0]*eye[1]*(z-eye[2]) + a[2]*eye[0]*(y-eye[1]) + a[1]*eye[2]*(x-eye[0])
             -a[2]*eye[1]*(x-eye[0]) - a[0]*eye[2]*(y-eye[1]) - a[1]*eye[0]*(z-eye[2]))
        dc = (a[0]*b[1]*eye[2] + a[2]*b[0]*eye[1] + a[1]*b[2]*eye[0]
             -a[2]*b[1]*eye[0] - a[0]*b[2]*eye[1] - a[1]*b[0]*eye[2])
        return gridpoint(x, y, z, da/d0, db/d0, -dc/d0, phase)

    def point_grid(self, x, y, z, phase):
        x, y, z = x - planecenter[0], y - planecenter[1], z - planecenter[2]
        return self.point_3d(x * gridscale, y * gridscale, z * zscale, phase)


l=101
values, vectors = diag_anderson(l, 0.5)
vector = vectors[24]
heights, phases = husimi(vector)
planecenter = (0.5*(len(heights) - 1), 0.5*(len(heights[0]) - 1), 0)
datagrid = [[None for j in range(len(heights[i]))] for i in range(len(heights))]

mygrid = grid()

for i in range(len(heights)):
    for j in range(len(heights[i])):
        datagrid[i][j] = mygrid.point_grid(i, j, heights[i][j]*1000, phases[i][j])

def triangle(p1, p2, p3, hue):
    ax, ay, az = p2.x_3d - p1.x_3d, p2.y_3d - p1.y_3d, p2.z_3d - p1.z_3d
    bx, by, bz = p3.x_3d - p1.x_3d, p3.y_3d - p1.y_3d, p3.z_3d - p1.z_3d
    axb = norm(ay*bz - az*by, az*bx - ax*bz, ax*by-ay*bx)
    e = norm(eye[0]-p1.x_3d, eye[1]-p1.y_3d, eye[2]-p1.z_3d)
    axb_r = axb[0]*e[0] + axb[1]*e[1] + axb[2]*e[2]
    depthpoint = mygrid.point_3d((p1.x_3d + p2.x_3d + p3.x_3d)/3.0,
                                 (p1.y_3d + p2.y_3d + p3.y_3d)/3.0, 0)
    return [depthpoint.depth,
            axb_r,
            path.path(path.moveto(p1.x_2d, p1.y_2d),
                      path.lineto(p2.x_2d, p2.y_2d),
                      path.lineto(p3.x_2d, p3.y_2d),
                      path.closepath()),
            hue]

def gethue(phase1, phase2):
    x1 = 0.5*phase1/math.pi
    x2 = 0.5*phase2/math.pi
    while x1-x2 > 0.5: x1 -= 1
    while x1-x2 < -0.5: x1 += 1
    dx = 0.5*(x1+x2)
    while dx > 1: dx -= 1
    while dx < 0: dx += 1
    return dx

triangles = []
for i in range(len(heights)-1):
    for j in range(len(heights[i])-1):
        midpoint = mygrid.point_3d(0.25 * (datagrid[i][j].x_3d + datagrid[i+1][j].x_3d + datagrid[i][j+1].x_3d + datagrid[i+1][j+1].x_3d),
                                   0.25 * (datagrid[i][j].y_3d + datagrid[i+1][j].y_3d + datagrid[i][j+1].y_3d + datagrid[i+1][j+1].y_3d),
                                   0.25 * (datagrid[i][j].z_3d + datagrid[i+1][j].z_3d + datagrid[i][j+1].z_3d + datagrid[i+1][j+1].z_3d))
        triangles.append(triangle(datagrid[i][j], datagrid[i+1][j], midpoint, gethue(datagrid[i][j].phase, datagrid[i+1][j].phase)))
        triangles.append(triangle(datagrid[i+1][j], datagrid[i+1][j+1], midpoint, gethue(datagrid[i+1][j].phase, datagrid[i+1][j+1].phase)))
        triangles.append(triangle(datagrid[i+1][j+1], datagrid[i][j+1], midpoint, gethue(datagrid[i+1][j+1].phase, datagrid[i][j+1].phase)))
        triangles.append(triangle(datagrid[i][j+1], datagrid[i][j], midpoint, gethue(datagrid[i][j+1].phase, datagrid[i][j].phase)))


triangles.sort()

c = canvas.canvas()

colors = [t[1] for t in triangles if t[1] > 0]
mincol = min(colors)
maxcol = max(colors)
for triangle in triangles:
    if triangle[1] < 0:
        c.fill(triangle[2], color.gray.black)
    else:
        usecolor = color.hsb(triangle[3], 1, 0.25 + 0.65 * ((triangle[1] - mincol)/(maxcol - mincol)) ** 0.5 )
        c.fill(triangle[2], usecolor)

c.writetofile("example")

