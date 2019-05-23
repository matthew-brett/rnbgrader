""" Test answers module
"""

import re

from rnbgrader.answers import raw2regex


def test_raw2regex():
    raw = r""" Min. 1st Qu.  Median    Mean 3rd Qu.    Max.    NA's 
        4.00   23.00   40.00   41.73   48.00  190.00     960 """
    assert re.search(raw2regex(raw), raw)


