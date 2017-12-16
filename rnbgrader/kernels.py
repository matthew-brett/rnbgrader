""" Utilities for using Jupyter kernels

Jupyter kernels are processes that accept messages and respond, following the
Jupyter messaging protocol.  See:

http://jupyter-client.readthedocs.io/en/stable/index.html
"""
# This file largely based on:
# https://github.com/jupyter/jupyter_kernel_test/blob/76684c6780edd56e66e94c833b2d5e808da354c9/jupyter_kernel_test/__init__.py
# That file is
# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

import io
from base64 import decodebytes
from queue import Empty

from PIL import Image
from jupyter_client.manager import start_new_kernel

DEFAULT_TIMEOUT = 15


class JupyterKernel(object):
    r""" Helper class to instantiate and use a Jupyter kernel

    Examples
    --------
    >>> kernel = JupyterKernel("ir")
    >>> outputs = kernel.run_code('a = 1\na')
    >>> len(outputs)
    1
    >>> outputs[0]['content']
    '1'
    """

    def __init__(self, kernel_name, timeout=DEFAULT_TIMEOUT):
        """ Initialize Jupyter kernel object

        Parameters
        ----------
        kernel_name : str
            Name of kernel.  For R, this is likely to be "ir" (see
            https://irkernel.github.io/docs/IRkernel).
        timeout : float, optional
            Default timeout in seconds.
        """
        self.km, self.kc = start_new_kernel(kernel_name=kernel_name)
        self.timeout = timeout

    def shutdown(self):
        """ Shutdown the kernel """
        self.kc.stop_channels()
        self.km.shutdown_kernel()

    def __del__(self):
        self.shutdown()

    def flush_channels(self):
        """ Flush all kernel channels """
        for channel in (self.kc.shell_channel, self.kc.iopub_channel):
            while True:
                try:
                    channel.get_msg(block=True, timeout=0.1)
                except Empty:
                    break

    def raw_run(self, code, timeout=None,
                 silent=False, store_history=True,
                 stop_on_error=True):
        """ Run code string, return reply and other output messages

        Parameters
        ----------
        code : str
            A string of code in the kernel's language.
        timeout : None or float, optional
            Timeout in seconds.  If None, use default timeout.
        silent : bool, optional (default False)
            If set, the kernel will execute the code as quietly possible, and
            will force store_history to be False.
        store_history : bool, optional
            If set, the kernel will store command history.  This is forced
            to be False if silent is True.
        stop_on_error: bool, optional (default True)
            Flag whether to abort the execution queue, if an exception is encountered.

        Returns
        -------
        reply : str
            Message dictionary giving kernel reply to code execute message.
        output_msgs : list
            List of other message dictionaries resulting from code execute message.
        """
        timeout = self.timeout if timeout is None else timeout

        msg_id = self.kc.execute(code=code, silent=silent,
                                 store_history=store_history,
                                 stop_on_error=stop_on_error)

        reply = self.kc.get_shell_msg(timeout=timeout)

        busy_msg = self.kc.iopub_channel.get_msg(timeout=1)
        assert busy_msg['content']['execution_state'] == 'busy'

        output_msgs = []
        while True:
            msg = self.kc.iopub_channel.get_msg(timeout=0.1)
            if msg['msg_type'] == 'status':
                assert msg['content']['execution_state'] == 'idle'
                break
            elif msg['msg_type'] == 'execute_input':
                assert msg['content']['code'] == code
                continue
            output_msgs.append(msg)

        return reply, output_msgs

    def _process_output(self, msg):
        if msg['msg_type'] == 'error':
            return dict(type='error',
                        message=msg,
                        content=msg['content']['evalue'])
        data = msg['content']['data']
        if msg['msg_type'] != 'display_data':
            raise RuntimeError("Don't recognize message type " +
                               msg['msg_type'])
        if 'image/png' in data:
            img_bytes = decodebytes(data['image/png'].encode('ascii'))
            png = Image.open(io.BytesIO(img_bytes))
            return dict(type='image',
                        message=msg,
                        content=png)
        if 'text/markdown' in data:
            return dict(type='text',
                        message=msg,
                        content=data['text/markdown'])
        raise RuntimeError("Don't recognize data {}".format(data))

    def run_code(self, code, timeout=None,
                 silent=False, store_history=True,
                 stop_on_error=True):
        """ Run code string, return list of processed results

        Parameters
        ----------
        code : str
            A string of code in the kernel's language.
        timeout : None or float, optional
            Timeout in seconds.  If None, use default timeout.
        silent : bool, optional (default False)
            If set, the kernel will execute the code as quietly possible, and
            will force store_history to be False.
        store_history : bool, optional
            If set, the kernel will store command history.  This is forced
            to be False if silent is True.
        stop_on_error: bool, optional (default True)
            Flag whether to abort the execution queue, if an exception is encountered.

        Returns
        -------
        outputs : list
            List of output dictionaries, one per output.  The outputs have been
            processed to convert mime types to text, images.
        """
        reply, output_msgs = self.raw_run(code, timeout, silent, store_history,
                                          stop_on_error)
        assert reply['header']['msg_type'] == 'execute_reply'
        return [self._process_output(msg) for msg in output_msgs]

    def clear(self):
        self.run_code('rm(list = ls())')
