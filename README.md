# RNBGrader - utilities for grading R Markdown notebooks

Utilities for grading notebooks in [R
Markdown](https://rmarkdown.rstudio.com)

Notebooks can be [R
notebooks](https://bookdown.org/yihui/rmarkdown/notebook.html) or
[Jupyter
notebooks](https://jupyter-notebook-beginner-guide.readthedocs.io/en/latest/what_is_jupyter.html)
converted to R Markdown with
[Jupytext](https://github.com/mwouts/jupytext)

## Quickstart

See the tests for examples.

## Installation

```
pip install rnbgrader
```

## Code

See <https://github.com/matthew-brett/rnbgrader>

Released under the BSD two-clause license - see the file `LICENSE`
in the source distribution.

[travis-ci](https://travis-ci.org/matthew-brett/rnbgrader) kindly
tests the code automatically under Python versions 3.6 through
3.8.

The latest released version is at
<https://pypi.python.org/pypi/rnbgrader>

## Tests

### R requirements

You need the R kernel installed for the tests.

On Mac:

```
brew install libgit2 harfbuzz fribidi
```

On Debian / Ubuntu:

```
sudo apt install -y libgit2-dev libharfbuzz-dev libfribidi-dev
```

On any platform:

```
Rscript -e "install.packages(c('repr', 'IRdisplay', 'crayon', 'pbdZMQ', 'devtools'))"
Rscript -e "devtools::install_github('IRkernel/IRkernel')"
Rscript -e "IRkernel::installspec()"
```

### The rest

*   Install `rnbgrader`
*   Install the test requirements:

    ```
    pip install -r test-requirements
    ```

*   Run the tests with:

    ```
    pytest rnbgrader
    ```

## Support

Please put up issues on the [rnbgrader issue
tracker](https://github.com/matthew-brett/rnbgrader/issues).
