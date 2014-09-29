import ctypes

def handle_keys(tid, keys):
	if not tid:
		print('Ouch! No main tid!')
		return
	if '<End>' in keys and len(keys) > 5:
		res = ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, ctypes.py_object(StopIteration))
		print('Interrupt result:', res)
