#!/usr/bin/env pythonw

import aidband
from functools import partial
import killable
import tkinter as tk
from time import sleep


aidband.raw_play_list(aidband.hotoptions.Favorites, doplay=False)
aidband.popen_kwargs = dict(creationflags=aidband.subprocess.CREATE_NO_WINDOW)


@killable.single_threaded
def update_song_title(root, song):
    root.title(song.artist + ' - ' + song.name)


class App(tk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.quit = False
        self.master = master
        self.master.iconbitmap('pixeldoctrine.ico')
        self.master.title('Aidband')
        self.master.minsize(600, 5)
        self.master.resizable(0,0)
        self.master.protocol('WM_DELETE_WINDOW', self.closing)
        self.create_widgets()
        self.pack(fill=tk.X)
        aidband.playing_callbacks += [partial(update_song_title, self.master)]
        t = killable.KillableThread(target=self.poll)
        t.start()
        aidband.play_idx()

    def create_widgets(self):
        self.cmd = tk.StringVar() 
        self.inp = tk.Entry(self, textvariable=self.cmd)
        self.inp.focus()
        for key in 'Return Left Right'.split():
            self.inp.bind('<'+key+'>', self.key)
        for i in range(1, 12+1):
            self.inp.bind('<F%i>'%i, self.key)
        self.inp.pack(fill=tk.X)

    def key(self, event):
        print(event)
        cmd = self.cmd.get()
        if event.keysym == 'Return':
            self.cmd.set('')
            aidband.play_search(cmd)
        elif event.keysym == 'F12':
            if aidband.stopped:
                aidband.play_idx()
            else:
                aidband.stop()
        elif len(event.keysym) >= 2 and event.keysym[0] == 'F':
            if event.state != 8:
                return
            fkey_idx = int(event.keysym[1:]) - 1
            self.cmd.set('')
            if len(aidband.hotoptions.all) > fkey_idx:
                ln = aidband.hotoptions.all[fkey_idx]
                aidband.play_list(ln)
        elif event.keysym == 'Left' and not cmd:
            aidband.prev_song()
        elif event.keysym == 'Right' and not cmd:
            aidband.next_song()

    def poll(self):
        while not self.quit:
            sleep(0.5)
            aidband.poll()

    def closing(self):
        print('terminating window')
        self.quit = True
        aidband.stop()
        self.master.destroy()

root = tk.Tk()
app = App(master=root)
app.mainloop()
