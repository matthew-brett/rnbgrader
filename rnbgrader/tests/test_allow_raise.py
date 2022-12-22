""" Test allow_raise
"""

from pathlib import Path
import re

import jupytext

from rnbgrader.allow_raise import skipper, write_skipped


TEST_DATA = Path(__file__).parent / 'data'
AR_IN_PTH = TEST_DATA / 'allow_raise_in.Rmd'
AR_OUT_PTH = TEST_DATA / 'allow_raise_out.Rmd'

YAML_HEADER = re.compile(r"\s*^---$.*?^---$", flags=re.S | re.M)


def rmd_equal(txt1, txt2):
    txt1 = YAML_HEADER.sub('', txt1)
    txt2 = YAML_HEADER.sub('', txt2)
    return txt1 == txt2


def test_skipper():
    nb = jupytext.read(AR_IN_PTH)
    proc_nb = skipper(nb)
    proc_txt = jupytext.writes(proc_nb, 'rmarkdown')
    assert rmd_equal(AR_OUT_PTH.read_text(), proc_txt)


def test_write_skipped(tmpdir):
    tmpdir = Path(tmpdir)
    in_nb_txt = AR_IN_PTH.read_text()
    exp_nb_txt = AR_OUT_PTH.read_text()
    tmp_nb_pth = tmpdir / 'in.Rmd'
    tmp_nb_pth.write_text(in_nb_txt)
    write_skipped(tmp_nb_pth)
    assert rmd_equal(tmp_nb_pth.read_text(), exp_nb_txt)
    tmp_nb_pth.write_text(in_nb_txt)
    tmp_out = tmpdir / 'out.Rmd'
    write_skipped(tmp_nb_pth, tmp_out)
    assert rmd_equal(tmp_nb_pth.read_text(), in_nb_txt)
    assert rmd_equal(tmp_out.read_text(), exp_nb_txt)
