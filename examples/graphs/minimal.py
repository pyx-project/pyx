from pyx import *

g = graph.graphxy(width=8)
g.plot(graph.data.file("minimal.dat", x=1, y=2))
g.writeEPSfile("minimal")

# the file minimal.dat looks like:
# 1  2
# 2  3
# 3  8
# 4  13
# 5  18
# 6  21

# graph styles can be modified by a second parameter to the plot method:
# g.plot(graph.data.file("minimal.dat", x=1, y=2), [graph.style.line()])
