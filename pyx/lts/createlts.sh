#!/bin/sh

latex createlts << EOF
10pt
article
10pt

EOF

latex createlts << EOF
11pt
article
11pt

EOF

latex createlts << EOF
12pt
article
12pt

EOF

latex createlts << EOF
10ptex
article
10pt
\usepackage{exscale}
EOF

latex createlts << EOF
11ptex
article
11pt
\usepackage{exscale}
EOF

latex createlts << EOF
12ptex
article
12pt
\usepackage{exscale}
EOF

latex createlts << EOF
foils17pt
foils
17pt

EOF

latex createlts << EOF
foils20pt
foils
20pt

EOF

latex createlts << EOF
foils25pt
foils
25pt

EOF

latex createlts << EOF
foils30pt
foils
30pt

EOF
