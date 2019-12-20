""" Test kernels module
"""
from functools import wraps

import PIL

from rnbgrader import JupyterKernel

import pytest

@pytest.fixture
def rkernel():
    # Inject kernel into test function namespace
    with JupyterKernel('ir') as rk:
        yield rk


def test_raw_run(rkernel):
    reply, msgs = rkernel.raw_run('plot(cars)')
    assert reply['header']['msg_type'] == 'execute_reply'
    assert len(msgs) == 1
    plot = msgs[0]['content']['data']
    assert 'image/png' in plot
    assert 'text/plain' in plot

    reply, msgs = rkernel.raw_run('a = 1')
    assert len(msgs) == 0
    reply, msgs = rkernel.raw_run('a')
    assert reply['header']['msg_type'] == 'execute_reply'
    assert len(msgs) == 1
    assert msgs[0]['content']['data']['text/markdown'] == '1'

    # Two show statements gives two output messages
    reply, msgs = rkernel.raw_run('b = 2')
    assert len(msgs) == 0
    reply, msgs = rkernel.raw_run('a\nb')
    assert reply['header']['msg_type'] == 'execute_reply'
    assert len(msgs) == 2
    assert msgs[0]['content']['data']['text/markdown'] == '1'
    assert msgs[1]['content']['data']['text/markdown'] == '2'


def _stripped(output):
    del output['message']
    return output


def test_clear_ns(rkernel):
    outputs = rkernel.run_code('a = 1')
    assert len(outputs) == 0
    outputs = rkernel.run_code('a')
    assert len(outputs) == 1
    assert _stripped(outputs[0]) == dict(type='text', content='[1] 1')
    rkernel.run_code('rm(list = ls())')
    outputs = rkernel.run_code('a')
    assert len(outputs) == 1
    assert outputs[0]['type'] == 'error'


def test_run_code(rkernel):
    output, = rkernel.run_code('a = 1\na')
    assert _stripped(output) == dict(type='text', content='[1] 1')
    output, = rkernel.run_code('plot(cars)')
    assert output['type'] == 'image'
    assert isinstance(output['content'], PIL.PngImagePlugin.PngImageFile)
    output, = rkernel.run_code('NULL')
    assert _stripped(output) == dict(type='text', content='NULL')
    output, = rkernel.run_code('print(1 + 2)')
    assert _stripped(output) == dict(type='stdout', content='[1] 3\n')


def test_context_manager():
    with JupyterKernel('ir') as rk:
        output, = rk.run_code('a = 1\na')
        assert _stripped(output) == dict(type='text', content='[1] 1')
