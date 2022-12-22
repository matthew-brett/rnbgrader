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


def skipper(nb):
    old_cells = deepcopy(nb.cells)
    kernel_name = nb['metadata'].get('kernelspec', {}).get('name')
    kernel = JupyterKernel(kernel_name)
    for i, cell in enumerate(old_cells):
        if cell['cell_type'] == 'code':
            msgs = kernel.run_code(cell['source'])
            if 'error' in [m['type'] for m in msgs]:
                add_raises_exception(cell)
        nb.cells[i] = cell
    return nb


def write_skipped(in_fname, out_fname=None):
    out_fname = in_fname if out_fname is None else out_fname
    nb_pth = Path(in_fname)
    in_txt = nb_pth.read_text()
    fmt, opts = jupytext.guess_format(in_txt, nb_pth.suffix)
    nb = jupytext.reads(in_txt, fmt=fmt)
    proc_nb = skipper(nb)
    jupytext.write(proc_nb, out_fname, fmt=fmt)


def get_parser():
    parser = ArgumentParser(description=__doc__,  # Usage from docstring
                            formatter_class=RawDescriptionHelpFormatter)
    parser.add_argument('notebook_fname',
                        help='Notebook filename')
    parser.add_argument(
        '-o', '--out-notebook',
        help='Name for notebook output (default overwrite input)')
    return parser


def main():
    parser = get_parser()
    args = parser.parse_args()
    write_skipped(args.notebook_fname, args.out_notebook)


if __name__ == '__main__':
    main()
