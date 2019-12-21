######################################################
RNBGrader - utilities for grading R Markdown notebooks
######################################################

.. shared-text-body

Utilities for grading notebooks in `R Markdown
<https://rmarkdown.rstudio.com>`_

Notebooks can be `R notebooks
<https://bookdown.org/yihui/rmarkdown/notebook.html>`_ or `Jupyter notebooks
<https://jupyter-notebook-beginner-guide.readthedocs.io/en/latest/what_is_jupyter.html>`_
converted to R Markdown with `Jupytext <https://github.com/mwouts/jupytext>`_

**********
Quickstart
**********

See the tests for examples.

************
Installation
************

::

    pip install rnbgrader

****
Code
****

See https://github.com/matthew-brett/rnbgrader

Released under the BSD two-clause license - see the file ``LICENSE`` in the
source distribution.

`travis-ci <https://travis-ci.org/matthew-brett/rnbgrader>`_ kindly tests the
code automatically under Python versions 3.6 through 3.8.

The latest released version is at https://pypi.python.org/pypi/rnbgrader

*****
Tests
*****

* Install ``rnbgrader``;
* Install the test requirements::

    pip install -r test-requirements

* Run the tests with::

    pytest rnbgrader

*******
Support
*******

Please put up issues on the `rnbgrader issue tracker`_.

.. standalone-references

.. |rnbgrader-documentation| replace:: `rnbgrader documentation`_
.. _rnbgrader documentation:
    https://matthew-brett.github.com/rnbgrader/rnbgrader.html
.. _documentation: https://matthew-brett.github.com/rnbgrader
.. _pandoc: http://pandoc.org
.. _jupyter: jupyter.org
.. _homebrew: brew.sh
.. _sphinx: http://sphinx-doc.org
.. _rest: http://docutils.sourceforge.net/rst.html
.. _rnbgrader issue tracker: https://github.com/matthew-brett/rnbgrader/issues
.. _pytest: https://pytest.org
.. _mock: https://github.com/testing-cabal/mock
