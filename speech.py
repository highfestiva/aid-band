#!/usr/bin/env python3

import pyttsx
engine = pyttsx.init()
engine.setProperty('rate', 130)
engine.setProperty('volume', 1.0)

def say(s):
	engine.say(s)
	engine.runAndWait()

if __name__ == '__main__':
	say('Ready to rock and roll!')
	say('Time to move on. Nothing to see folks, nothing to see. Bye!')
