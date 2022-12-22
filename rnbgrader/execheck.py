""" Execute checks for notebooks
"""

import sys
import os.path as op
from argparse import ArgumentParser

import pandas as pd

try:  # Newer nbclient
    from nbclient import execute as executenb
    from nbclient.exceptions import CellExecutionError
except ImportError:
    from nbconvert.preprocessors.execute import executenb, CellExecutionError

import jupyter_client

import jupytext

MSG_COLNAME = 'error message'


def get_lang2kernel_name():
    names = list(jupyter_client.kernelspec.find_kernel_specs())
    lang2kernel_name = {}
    for name in names:
        spec = jupyter_client.kernelspec.get_kernel_spec(name)
        lang2kernel_name[spec.language] = name
        # Apparently language can also follow kernel name
        if name not in lang2kernel_name:
            lang2kernel_name[name] = name
    return lang2kernel_name


LANG2KERNEL_NAME = get_lang2kernel_name()


def nb2lang(nb):
    """ Detect language of notebook `nb`

    Parameters
    ----------
    nb : dict
        Notebook dictionary.

    Returns
    -------
    lang : str
        Detected language.
    """
    metadata = nb['metadata']
    if 'kernelspec' in metadata:
        # Probably a Jupyter notebook
        return metadata['kernelspec']['name']
    # Guess from main_language
    return metadata['jupytext'].get('main_language', 'R')


def nb2kernel_name(nb):
    """ Return kernel name for notebook `nb`

    Parameters
    ----------
    nb : dict
        Notebook dictionary.

    Returns
    -------
    kernel_name : str
        Jupyter kernel name.
    """
    return LANG2KERNEL_NAME[nb2lang(nb)]


def exe_check_nb_fname(nb_fname, wd=None):
    """ Execute notebook, return error message or 'ok'

    Parameters
    ----------
    nb_fname : str
        Filename of notebook to execute.
    wd : None or str
        Directory in which to execute notebook.  None means use directory
        containing `nb_fname`

    Returns
    -------
    err_msg : str
        Error message or 'ok' for no error.
    """
    wd = op.dirname(nb_fname) if wd is None else wd
    nb = jupytext.read(nb_fname)
    try:
        executenb(nb, cwd=wd, kernel_name=nb2kernel_name(nb))
    except CellExecutionError as e:
        return str(e)
    return 'ok'


def do_exe_checks(nb_fnames,
                  wd=None,
                  in_filter_fname=None,
                  out_filter_fname=None,
                  fails_only=False,
                 ):
    out = (pd.read_csv(in_filter_fname, index_col=0)[MSG_COLNAME]
           if in_filter_fname else pd.Series(name=MSG_COLNAME, dtype=object))
    for nb_fname in nb_fnames:
        if nb_fname in out.index and out.loc[nb_fname] == 'ok':
            continue
        out.loc[nb_fname] = exe_check_nb_fname(nb_fname, wd=wd)
    if out_filter_fname:
        out.to_csv(out_filter_fname, header=True)
    if fails_only:
        return out.loc[out != 'ok']
    return out


def main():
    parser = ArgumentParser()
    parser.add_argument('nb_fnames', nargs='+', help='Notebook filename(s)')
    parser.add_argument('--cwd',
                        help='Directory in which to run notebooks')
    parser.add_argument('--in-filter',
                        help='Filename with table of previous results')
    parser.add_argument('--out-filter',
                        help='Filename to which to write result table')
    parser.add_argument('--fails-only', action='store_true',
                        help='If set, only show results for failed notebooks')
    args = parser.parse_args()
    results = do_exe_checks(args.nb_fnames,
                            args.cwd,
                            args.in_filter,
                            args.out_filter,
                            args.fails_only)
    for fn, result in results.iteritems():
        print(f'{fn:40s}: {result}')


def old_main():
    # Deprecate old command name.
    sys.stderr.write('Please use "rnbg-exe-check" command instead\n')
    sys.stderr.write('This command name will go away in some future version\n')
    main()
