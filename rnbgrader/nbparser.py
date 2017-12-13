""" R Notebook parser

Parse R notebook in R Markdown.

Extract code chunks from notebook.
"""

from mistune import preprocessing, BlockLexer

BLOCK = BlockLexer()


def read_file(file_ish):
    """ Read and return string contents of notebook in `file_ish`
    """
    if hasattr(file_ish, 'read'):
        return file_ish.read()
    with open(file_ish, 'rt', encoding='utf8') as fobj:
        return fobj.read()


def load(file_ish):
    """ Read contents of `file_ish`, return as parsed notebook.
    """
    return loads(read_file(file_ish))


def loads(nb_str):
    """ Parse string `nb_str`, return as parsed notebook.
    """
    BLOCK.tokens[:] = []
    return BLOCK(preprocessing(nb_str))


def as_chunks(nb_obj):
    """ Extract chunks from parsed notebook `nb_obj`
    """
    return [p for p in nb_obj if p['type'] == 'code']
