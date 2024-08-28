#!/usr/bin/env python3
""" Add skip-exceptions to notebook cells raising errors.
"""

from pathlib import Path
from argparse import ArgumentParser, RawDescriptionHelpFormatter
from copy import deepcopy

import jupytext

from .kernels import JupyterKernel


def add_raises_exception(cell):
    meta = cell['metadata']
    if not 'tags' in meta:
        meta['tags'] = []
    if not 'raises-exception' in meta['tags']:
        meta['tags'].append('raises-exception')


def skipper(nb, print_err=True, **kwargs):
    r""" Run notebook `nb`, add skip markup to cells causing error

    Parameters
    ----------
    nb : dict
        Jupyter notebook
    print_err: {True, False}, optional
        Print error messages.
    \*\*kwargs : dict, optional
        Arguments to be passed to :class:`JupyterKernel`, such as ``cwd``

    Returns
    -------
    skipped_nb : dict
        Jupyter notebook with allow-raise markup added to metadata for erroring
        cells.
    """
    nb = deepcopy(nb)
    old_cells = deepcopy(nb.cells)
    kernel_name = nb['metadata'].get('kernelspec', {}).get('name')
    kernel = JupyterKernel(kernel_name, **kwargs)
    errors = []
    for i, cell in enumerate(old_cells):
        if cell['cell_type'] == 'code':
            msgs = kernel.run_code(cell['source'])
            err_msgs = [m for m in msgs if m['type'] == 'error']
            if err_msgs:
                add_raises_exception(cell)
                errors += err_msgs
        nb.cells[i] = cell
    return nb, errors


def write_skipped(in_fname, out_fname=None, show_errors=False, **kwargs):
    out_fname = in_fname if out_fname is None else out_fname
    nb_pth = Path(in_fname)
    in_txt = nb_pth.read_text()
    fmt, opts = jupytext.guess_format(in_txt, nb_pth.suffix)
    nb = jupytext.reads(in_txt, fmt=fmt)
    proc_nb, errors = skipper(nb, cwd=nb_pth.parent, **kwargs)
    jupytext.write(proc_nb, out_fname, fmt=fmt)
    if show_errors and errors:
        print(f'Errors for {nb_pth}')
        for error in errors:
            print(error['content'])


def get_parser():
    parser = ArgumentParser(description=__doc__,  # Usage from docstring
                            formatter_class=RawDescriptionHelpFormatter)
    parser.add_argument('notebook_fname', nargs='+',
                        help='Notebook filename')
    parser.add_argument(
        '-o', '--out-notebook',
        help='Name for notebook output (default overwrite input)')
    parser.add_argument(
        '-E', '--show-errors', action='store_true',
        help='If set, display errors for notebook cells')
    return parser


def main():
    parser = get_parser()
    args = parser.parse_args()
    if len(args.notebook_fname) > 1:
        if args.out_notebook:
            raise RuntimeError('out-notebook option only valid'
                               'for single notebook input')
        for nb_fname in args.notebook_fname:
            write_skipped(nb_fname, show_errors=args.show_errors)
    else:
        write_skipped(args.notebook_fname[0], args.out_notebook)


if __name__ == '__main__':
    main()
