""" Class to run notebooks and return report
"""

from .kernels import JupyterKernel


class EvaluatedChunk:

    def __init__(self, chunk, results=None):
        self.chunk = chunk
        self.results = results

    def __eq__(self, other):
        return self.__dict__ == other.__dict__


class ChunkRunner(object):

    def __init__(self, chunks, kernel='ir', stop_on_error=True):
        """ Initialize notebook runner

        Parameters
        ----------
        chunks : sequence of chunks
            Sequence of notebook code chunk instances.
        kernel : string or kernel instance, optional
            Can be string giving kernel name, or kernel instance.
        stop_on_error : {True, False}, optional
            Whether to stop evaluating chunks at first error.

        Attributes
        ----------
        chunks : as above
        stop_on_error : as above
        results : sequence of EvaluatedChunk, property
        outcome : {'ok', 'error'}, property
        messages : None or str, property
        """
        self.chunks = chunks
        self._init_kernel(kernel)
        self.stop_on_error = stop_on_error
        self._results = None
        self._outcome = None
        self._message = None
        self._execute()

    def __del__(self):
        if self._own_kernel:
            self._kernel.shutdown()

    def get_kernel(self):
        return self._kernel

    def set_kernel(self, kernel='ir'):
        """ Set kernel from str or kernel instance

        If input `kernel` argument was a string, `kernel` is a new kernel
        created for this instance.
        """
        del self._kernel
        self._init_kernel(kernel)

    def _init_kernel(self, kernel):
        self._own_kernel = not hasattr(kernel, 'run_code')
        self._kernel = JupyterKernel(kernel) if self._own_kernel else kernel

    @property
    def results(self):
        """ Sequence of :class:`EvaluatedChunk` """
        return self._results

    @property
    def outcome(self):
        """ 'ok' if all chunks evaluated without error, 'error' otherwise.
        """
        return self._outcome

    @property
    def message(self):
        """ None if no error running chunks, otherwise string

        String contains all error messages, if `stop_if_error` is False.
        """
        return self._message

    def _report_errors(self, chunk, errors):
        return 'Errors for chunk at line no {}:\n----{}\n---\n{}\n'.format(
            chunk.start_line + 1,
            chunk.code,
            'Error:\n{}'.join(e['content'] for e in errors))

    def _execute(self, force=False):
        """ Execute code chunks, filling results

        Parameters
        ----------
        force : {False, True}
            If False, and the results are already present, return without
            action. Otherwise, rerun the chunks and fill the results.
        """
        if not force and self._results is not None:
            return
        results = []
        any_error = False
        messages = []
        for chunk in self.chunks:
            if any_error and self.stop_on_error:
                results.append(EvaluatedChunk(chunk))
                continue
            outputs = self._kernel.run_code(
                chunk.code,
                stop_on_error=self.stop_on_error)
            results.append(EvaluatedChunk(chunk, outputs))
            errors = [p for p in outputs if p['type'] == 'error']
            if len(errors) != 0:
                messages.append(self._report_errors(chunk, errors))
                any_error = True
        self._results = tuple(results)
        self._outcome = "error" if any_error else 'ok'
        self._message = '\n\n'.join(messages) if len(messages) > 0 else None
