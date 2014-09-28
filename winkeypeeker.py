import re
import sys
from time import time
from threading import Thread
import tkinter as tk

keys = ''
hittime = None

def _timeout(t):
	global hittime
	if hittime and time()-hittime > t:
		hittime = time()
		return True
	return False

def peekstr(timeout=10):
	if _timeout(timeout):
		global keys
		keys = ''
	elif re.match('^[^<>+-]+\r$', keys):
		return getstr()
	elif re.match('^[^<>+-]+$', keys):
		# Not finished typing yet.
		return ''
	# Possibly hotkey or such.
	return getstr()

def getstr():
	global keys
	ks = keys
	keys = ''
	return ks

def _key(event):
	global keys,hittime
	if event.char == '\b':
		keys = keys[:len(keys)-1] if keys else ''
	elif event.char:
		keys += event.char
	elif '_' not in event.keysym:
		keys += '<'+event.keysym+'>'
	hittime = time()

def _die(root):
	global keys
	keys = '<quit>'
	hittime = time()
	root.quit()

def main():
	root = tk.Tk()
	root.geometry('300x200')
	root.bind('<KeyPress>', _key)
	root.attributes("-topmost", True)
	#root.overrideredirect(1)
	root.protocol("WM_DELETE_WINDOW", lambda: _die(root))
	root.mainloop()
	sys.exit(0)

Thread(target=main).start()
