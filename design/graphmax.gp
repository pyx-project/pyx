set term post
set out 'graphmax.ps'
set xrange [0:1]
set yrange [0:2]
a=0
b=1
z1=0.5
z2=0.3
z3=0.1
plot ((z1 - a) * log((z1 - a) / (x - a)) + (b - z1) * log((b - z1) / (b - x))) / (b - a) title "xmin=0.5",\
     ((z2 - a) * log((z2 - a) / (x - a)) + (b - z2) * log((b - z2) / (b - x))) / (b - a) title "xmin=0.3",\
     ((z3 - a) * log((z3 - a) / (x - a)) + (b - z3) * log((b - z3) / (b - x))) / (b - a) title "xmin=0.1"
set xrange [0:10]
b=10
z1=5
z2=3
z3=1
plot ((z1 - a) * log((z1 - a) / (x - a)) + (b - z1) * log((b - z1) / (b - x))) / (b - a) title "xmin=5",\
     ((z2 - a) * log((z2 - a) / (x - a)) + (b - z2) * log((b - z2) / (b - x))) / (b - a) title "xmin=3",\
     ((z3 - a) * log((z3 - a) / (x - a)) + (b - z3) * log((b - z3) / (b - x))) / (b - a) title "xmin=1"
