#!/usr/bin/env python3

try:
	import pyttsx
	engine = pyttsx.init()
	def say(s):
		wpm = 130 if len(s)>20 else 110
		engine.setProperty('rate', wpm)
		engine.say(s)
		engine.runAndWait()
except:
	print('Speech not available, pip install pyttsx to get it...')
	def say(s):
		pass


if __name__ == '__main__':
	say('Ready to rock and roll!')
