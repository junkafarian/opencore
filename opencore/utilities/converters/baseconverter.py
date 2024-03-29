import errno
import os
import signal
import shlex
from subprocess import Popen
from subprocess import PIPE
import threading
import tempfile
import time

from zope.interface import implements
from opencore.utilities.converters.interfaces import IConverter

class BaseConverterError(Exception):
    pass

class BaseConverter:
    """ Base class for all converters """

    content_type = None
    content_description = None
    timeout = 5

    implements(IConverter)

    def __init__(self):
        if not self.content_type:
            raise BaseConverterError('content_type undefinied')

        if not self.content_description:
            raise BaseConverterError('content_description undefinied')

    def execute(self, com):
        out = tempfile.TemporaryFile()
        args = shlex.split(com)
        PO = Popen(args, shell=False, stdout=out, stdin=PIPE, stderr=PIPE,
                   close_fds=True)
        timeout = _ProcTimeout(PO, timeout=self.timeout)
        timeout.start()
        try:
            PO.communicate()
        except OSError, e:
            if e.errno != errno.ECHILD: # No child process
                raise
            # else:
            #    subprocess finished so quickly that os.wait() call failed
            #    an ignorable error.

        timeout.stop()
        timeout.join()
        out.seek(0)
        return out

    def getDescription(self):
        return self.content_description

    def getType(self):
        return self.content_type

    def getDependency(self):
        return getattr(self, 'depends_on', None)

    def __call__(self, s):
        return self.convert(s)

    def isAvailable(self):

        depends_on = self.getDependency()
        if depends_on:
            try:
                cmd = 'which %s' % depends_on
                PO =  Popen(cmd, shell=True, stdout=PIPE, close_fds=True)
            except OSError:
                return 'no'
            else:
                out = PO.stdout.read()
                PO.wait()
                del PO
            if (
                ( out.find('no %s' % depends_on) > - 1 ) or
                ( out.lower().find('not found') > -1 ) or
                ( len(out.strip()) == 0 )
                ):
                return 'no'
            return 'yes'
        else:
            return 'always'


class _ProcTimeout(threading.Thread):
    """
    Implements a timeout on a running subprocess.  Polls subprocess on a
    separate thread to see if it has finished running.  If process has not
    finished by the time the timeout has expired, it then attempts to terminate
    the process.

    Some external converter programs (wvConvert) have been known to hang
    indefinitely with certain inputs.
    """
    def __init__(self, process, poll_interval=.01, timeout=5):
        super(_ProcTimeout, self).__init__()
        self.process = process
        self.poll_interval = poll_interval
        self.timeout = timeout
        self._run = True

    def run(self):
        start_time = time.time()
        process = self.process
        poll_interval = self.poll_interval
        timeout = self.timeout
        time.sleep(poll_interval)
        while self._run and not process.poll():
            elapsed = time.time() - start_time
            # Will (hopefully) fail quietly on Windows
            # Occasionally it seems that process.poll() tells us we are
            # still running even when we're not, so we check the error
            # status code from os.system() and break out if there is an
            # error, usually because there is no such process.
            if elapsed > timeout * 2:
                os.kill(process.pid, signal.SIGKILL)
            elif elapsed > timeout:
                os.kill(process.pid, signal.SIGTERM)
            time.sleep(poll_interval)

    def stop(self):
        self._run = False
