import sys
if sys.path[0] != "../..":
    sys.path.insert(0, "../..")

import unittest

from pyx import *
from pyx.path import *

epsilon = 1e-5
def isEqual(l1, l2):
    return abs(unit.topt(l1-l2))<epsilon


class NormpathTestCase(unittest.TestCase):
    def testsplit(self):
        p = path(moveto(0,0), lineto(1,0), moveto(2,0), lineto(3,0))
        np = normpath(p)

        # one split parameter
        sp = np.split([0])
        assert len(sp)==2 and sp[0] is None and isEqual(sp[1].arclen(), 2)
        
        sp = np.split([0.5])
        assert len(sp)==2 and isEqual(sp[0].arclen(), 0.5) and isEqual(sp[1].arclen(), 1.5)
        
        sp = np.split([1])
        assert len(sp)==2 and isEqual(sp[0].arclen(), 1) and isEqual(sp[1].arclen(), 1)
        
        sp = np.split([1.5])
        assert len(sp)==2 and isEqual(sp[0].arclen(), 1.5) and isEqual(sp[1].arclen(), 0.5)
        
        sp = np.split([2])
        assert len(sp)==2 and isEqual(sp[0].arclen(), 2) and sp[1] is None

        # two split parameters
        sp = np.split([0, 0.5])
        assert len(sp)==3 and sp[0] is None and isEqual(sp[1].arclen(), 0.5) and isEqual(sp[2].arclen(), 1.5)
        
        sp = np.split([0, 1])
        assert len(sp)==3 and sp[0] is None and isEqual(sp[1].arclen(), 1) and isEqual(sp[2].arclen(), 1)

        sp = np.split([0, 1.5])
        assert len(sp)==3 and sp[0] is None and isEqual(sp[1].arclen(), 1.5) and isEqual(sp[2].arclen(), 0.5)
        
        sp = np.split([0, 2])
        assert len(sp)==3 and sp[0] is None and isEqual(sp[1].arclen(), 2) and sp[2] is None

        sp = np.split([0.5, 1])
        assert len(sp)==3 and isEqual(sp[0].arclen(), 0.5) and isEqual(sp[1].arclen(), 0.5) and isEqual(sp[2].arclen(), 1)

        sp = np.split([0.5, 1.5])
        assert len(sp)==3 and isEqual(sp[0].arclen(), 0.5) and isEqual(sp[1].arclen(), 1) and isEqual(sp[2].arclen(), 0.5)

        sp = np.split([0.5, 2])
        assert len(sp)==3 and isEqual(sp[0].arclen(), 0.5) and isEqual(sp[1].arclen(), 1.5) and sp[2] is None

        sp = np.split([1, 1.5])
        assert len(sp)==3 and isEqual(sp[0].arclen(), 1) and isEqual(sp[1].arclen(), 0.5) and isEqual(sp[2].arclen(), 0.5)

        sp = np.split([1, 2])
        assert len(sp)==3 and isEqual(sp[0].arclen(), 1) and isEqual(sp[1].arclen(), 1) and sp[2] is None

        sp = np.split([1.5, 2])
        assert len(sp)==3 and isEqual(sp[0].arclen(), 1.5) and isEqual(sp[1].arclen(), 0.5) and sp[2] is None
        
        # three split parameters
        sp = np.split([0, 0.5, 1])
        assert len(sp)==4 and sp[0] is None and isEqual(sp[1].arclen(), 0.5) and isEqual(sp[2].arclen(), 0.5) and isEqual(sp[3].arclen(), 1)

        sp = np.split([0, 0.5, 1.5])
        assert len(sp)==4 and sp[0] is None and isEqual(sp[1].arclen(), 0.5) and isEqual(sp[2].arclen(), 1) and isEqual(sp[3].arclen(), 0.5)

        sp = np.split([0, 0.5, 2])
        assert len(sp)==4 and sp[0] is None and isEqual(sp[1].arclen(), 0.5) and isEqual(sp[2].arclen(), 1.5) and sp[3] is None

        sp = np.split([0, 1, 1.5])
        assert len(sp)==4 and sp[0] is None and isEqual(sp[1].arclen(), 1) and isEqual(sp[2].arclen(), 0.5) and isEqual(sp[3].arclen(), 0.5)

        sp = np.split([0, 1, 2])
        assert len(sp)==4 and sp[0] is None and isEqual(sp[1].arclen(), 1) and isEqual(sp[2].arclen(), 1) and sp[3] is None
        

        sp = np.split([0, 1.5, 2])
        assert len(sp)==4 and sp[0] is None and isEqual(sp[1].arclen(), 1.5) and isEqual(sp[2].arclen(), 0.5) and sp[3] is None

        sp = np.split([0.5, 1, 1.5])
        assert len(sp)==4 and isEqual(sp[0].arclen(), 0.5) and isEqual(sp[1].arclen(), 0.5) and isEqual(sp[2].arclen(), 0.5) and isEqual(sp[3].arclen(), 0.5)

        sp = np.split([0.5, 1.5, 2])
        assert len(sp)==4 and isEqual(sp[0].arclen(), 0.5) and isEqual(sp[1].arclen(), 1) and isEqual(sp[2].arclen(), 0.5) and sp[3] is None

        sp = np.split([1, 1.5, 2])
        assert len(sp)==4 and isEqual(sp[0].arclen(), 1) and isEqual(sp[1].arclen(), 0.5) and isEqual(sp[2].arclen(), 0.5) and sp[3] is None


        # four split parameters
        sp = np.split([0, 0.5, 1, 1.5])
        assert len(sp)==5 and sp[0] is None and isEqual(sp[1].arclen(), 0.5) and isEqual(sp[2].arclen(), 0.5) and isEqual(sp[3].arclen(), 0.5) and isEqual(sp[4].arclen(), 0.5)

        sp = np.split([0, 0.5, 1, 2])
        assert len(sp)==5 and sp[0] is None and isEqual(sp[1].arclen(), 0.5) and isEqual(sp[2].arclen(), 0.5) and isEqual(sp[3].arclen(), 1) and sp[4] is None

        sp = np.split([0, 0.5, 1.5, 2])
        assert len(sp)==5 and sp[0] is None and isEqual(sp[1].arclen(), 0.5) and isEqual(sp[2].arclen(), 1) and isEqual(sp[3].arclen(), 0.5) and sp[4] is None

        sp = np.split([0, 1, 1.5, 2])
        assert len(sp)==5 and sp[0] is None and isEqual(sp[1].arclen(), 1) and isEqual(sp[2].arclen(), 0.5) and isEqual(sp[3].arclen(), 0.5) and sp[4] is None

        sp = np.split([0.5, 1, 1.5, 2])
        assert len(sp)==5 and isEqual(sp[0].arclen(), 0.5) and isEqual(sp[1].arclen(), 0.5) and isEqual(sp[2].arclen(), 0.5) and isEqual(sp[3].arclen(), 0.5) and sp[4] is None

        
        # five split parameters
        sp = np.split([0, 0.5, 1, 1.5, 2])
        assert len(sp)==6 and sp[0] is None and isEqual(sp[1].arclen(), 0.5) and isEqual(sp[2].arclen(), 0.5) and isEqual(sp[3].arclen(), 0.5) and isEqual(sp[4].arclen(), 0.5) and sp[5] is None


if __name__ == "__main__":
    unittest.main()
