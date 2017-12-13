""" Test kernels module
"""

from rnbgrader import JupyterKernel


def test_kernels():
    rk = JupyterKernel('ir')
    reply, msgs = rk.run_code('plot(cars)')
    assert len(msgs) == 1
    plot = msgs[0]['content']['data']
    assert 'image/png' in plot
    assert 'text/plain' in plot

    reply, msgs = rk.run_code('a = 1')
    assert len(msgs) == 0
    reply, msgs = rk.run_code('a')
    assert len(msgs) == 1
    assert msgs[0]['content']['data']['text/markdown'] == '1'

    # Two show statements gives two output messages
    reply, msgs = rk.run_code('b = 2')
    assert len(msgs) == 0
    reply, msgs = rk.run_code('a\nb')
    assert len(msgs) == 2
    assert msgs[0]['content']['data']['text/markdown'] == '1'
    assert msgs[1]['content']['data']['text/markdown'] == '2'
