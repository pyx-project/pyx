# contributed by Stephen Phillips

from pyx import *

# Mandelbrot parameters
re_min = -2
re_max = 0.5
im_min = -1.25
im_max = 1.25
gridx = 100
gridy = 100
max_iter = 10

# Set-up
re_step = (re_max - re_min) / gridx
im_step = (im_max - im_min) / gridy
d = []

# Compute fractal
for re_index in range(gridx):
    re = re_min + re_step * (re_index + 0.5)
    for im_index in range(gridy):
        im = im_min + im_step * (im_index + 0.5)
        c = complex(re, im)
        n = 0
        z = complex(0, 0)
        while n < max_iter and abs(z) < 2:
            z = (z * z) + c
            n += 1
        d.append([re - 0.5 * re_step, re + 0.5 * re_step,
                  im - 0.5 * im_step, im + 0.5 * im_step,
                  float(n)/max_iter])

# Plot graph
g = graph.graphxy(height=8, width=8,
                  x=graph.axis.linear(min=re_min, max=re_max, title=r'$\Re(c)$'),
                  y=graph.axis.linear(min=im_min, max=im_max, title=r'$\Im(c)$'))
g.plot(graph.data.list(d, xmin=1, xmax=2, ymin=3, ymax=4, color=5),
       [graph.style.rect(color.palette.Rainbow)])
g.dodata() # plot data first, then axes
g.writeEPSfile('mandel')
