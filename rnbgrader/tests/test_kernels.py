""" Test kernels module
"""

import PIL

from rnbgrader import JupyterKernel


def test_raw_run():
    rk = JupyterKernel('ir')
    reply, msgs = rk.raw_run('plot(cars)')
    assert reply['header']['msg_type'] == 'execute_reply'
    assert len(msgs) == 1
    plot = msgs[0]['content']['data']
    assert 'image/png' in plot
    assert 'text/plain' in plot

    reply, msgs = rk.raw_run('a = 1')
    assert len(msgs) == 0
    reply, msgs = rk.raw_run('a')
    assert reply['header']['msg_type'] == 'execute_reply'
    assert len(msgs) == 1
    assert msgs[0]['content']['data']['text/markdown'] == '1'

    # Two show statements gives two output messages
    reply, msgs = rk.raw_run('b = 2')
    assert len(msgs) == 0
    reply, msgs = rk.raw_run('a\nb')
    assert reply['header']['msg_type'] == 'execute_reply'
    assert len(msgs) == 2
    assert msgs[0]['content']['data']['text/markdown'] == '1'
    assert msgs[1]['content']['data']['text/markdown'] == '2'


def _stripped(output):
    del output['message']
    return output


def test_clear():
    rk = JupyterKernel('ir')
    outputs = rk.run_code('a = 1')
    assert len(outputs) == 0
    outputs = rk.run_code('a')
    assert len(outputs) == 1
    assert _stripped(outputs[0]) == dict(type='text', content='1')
    rk.clear()
    outputs = rk.run_code('a')
    assert len(outputs) == 1
    assert outputs[0]['type'] == 'error'


def test_run_code():
    rk = JupyterKernel('ir')
    output, = rk.run_code('a = 1\na')
    assert _stripped(output) == dict(type='text', content='1')
    output, = rk.run_code('plot(cars)')
    assert output['type'] == 'image'
    assert isinstance(output['content'], PIL.PngImagePlugin.PngImageFile)
    output, = rk.run_code('NULL')
    assert _stripped(output) == dict(type='text', content='NULL')
    output, = rk.run_code('print(1 + 2)')
    assert _stripped(output) == dict(type='stdout', content='[1] 3\n')
