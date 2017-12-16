""" Class to run notebooks and return report
"""

from .kernels import JupyterKernel


class NotebookRunner(object):

    def __init__(self, notebook, kernel='ir', stop_on_error=True):
        """ Initialize notebook runner

        Parameters
        ----------
        notebook : notebook instance
        kernel : string or kernel instance, optional
            Can be string giving kernel name, or kernel instance.
        stop_on_error : {True, False}, optional
            Whether to stop evaluating notebook at first error.
        """
        self.notebook = notebook
        self._own_kernel = not hasattr(kernel, 'km')
        self.kernel = JupyterKernel(kernel) if self._own_kernel else kernel
        self.stop_on_error = stop_on_error
        self._results = None
        self._outcome = None
        self._message = None

    def __del__(self):
        if self._own_kernel:
            self.kernel.shutdown()

    @property
    def results(self):
        self._execute()
        return self._results

    @property
    def outcome(self):
        self._execute()
        return self._outcome

    @property
    def message(self):
        self._execute()
        return self._message

    def _report_errors(self, chunk, errors):
        return 'Errors for chunk at line no {}:\n----{}\n---\n{}\n'.format(
            chunk.line_no,
            chunk.code,
            'Error:\n{}'.join(e['content'] for e in errors))

    def _execute(self, force=False):
        if not force and self._results is not None:
            return
        results = []
        any_error = False
        messages = []
        for chunk in self.notebook.chunks:
            if any_error and self.stop_on_error:
                results.append((chunk, None))
                continue
            outputs = self.kernel.run_code(
                chunk.code,
                stop_on_error=self.stop_on_error)
            results.append((chunk, outputs))
            errors = [p for p in outputs if p['type'] == 'error']
            if len(errors) != 0:
                messages.append(self._report_errors(chunk, errors))
                any_error = True
        self._results = tuple(results)
        self._outcome = "error" if any_error else 'ok'
        self._message = '\n\n'.join(messages) if len(messages) > 0 else None
