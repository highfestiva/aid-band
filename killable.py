#!/usr/bin/env python3

import sys
from threading import Thread

class KillableThread(Thread):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.daemon = True
    def _bootstrap(self):
        self._killme = False
        sys.settrace(self._trace)
        super()._bootstrap()
    def stop(self):
        self._killme = True
    def _trace(self, frame, event, arg):
        if self._killme:
            sys.exit(0)
        return self._trace

def kill_self():
    try:
        import win32process
        win32process.ExitProcess(0)
    except:
        pass
    try:
        import os,signal
        os.kill(os.getpid(), signal.SIGKILL)
    except:
        pass
    print('Might have to kill this one with Ctrl+C...')
    sys.exit(0)
