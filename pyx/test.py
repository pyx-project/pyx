from canvas import *
from path import *
import profile
import pstats

def test():
    c1=canvas()

    p=path([moveto(0,0)])

    for i in xrange(5000):
        p.append(lineto(i,i))

    c1.draw(p)

    c1.write("test.eps", 21, 29.7)

profile.run('test()', 'test.prof')
pstats.Stats("test.prof").sort_stats('time').print_stats(10)
