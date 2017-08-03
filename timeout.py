#!/usr/bin/env python

from time import time

class Timeout:
    def __init__(self):
        self.reset()
    def timeout(self,t):
        return time()-self._hittime > t
    def reset(self):
        self._hittime = time()
