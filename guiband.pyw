#!/usr/bin/env pythonw

import sys
sys.stdout = sys.stderr = open('gui.log', 'w')
print('guiband running')
import aidband
from functools import partial
import killable
import tkinter as tk
from time import sleep


aidband.raw_play_list(aidband.hotoptions.Favorites, doplay=False)
aidband.popen_kwargs = dict(creationflags=aidband.subprocess.CREATE_NO_WINDOW)
current_title = ''


@killable.single_threaded
def update_song_title(root, song):
    global current_title
    if not song:
        current_title = '[Stopped]'
    else:
        current_title = song.artist + ' - ' + song.name
    root.title(current_title)


class App(tk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.master.bind("<Button-1>", self.next_song)
        self.master.bind("<Button-3>", self.prev_song)
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
        for key in 'Return Left Right Tab'.split():
            self.inp.bind('<'+key+'>', self.key)
        for i in range(1, 12+1):
            self.inp.bind('<F%i>'%i, self.key)
        self.inp.pack(fill=tk.X)

    def key(self, event):
        print(event)
        cmd = self.cmd.get()
        if event.keysym == 'Return':
            self.cmd.set('')
            if cmd.startswith('!'):
                aidband.run_command(cmd)
            else:
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
        elif event.keysym == 'Tab':
            shuffle = aidband.toggle_shuffle()
            root.title(current_title + (' [shuffled]' if shuffle else ' [playing in order]'))

    def next_song(self, *args, **kwargs):
        self.cmd.set('')
        aidband.next_song()

    def prev_song(self, *args, **kwargs):
        self.cmd.set('')
        aidband.prev_song()

    def drop_song(self, *args, **kwargs):
        self.cmd.set('')
        aidband.drop_song()

    def poll(self):
        while not self.quit:
            sleep(1)
            aidband.poll()
            cmd = self.cmd.get()
            if cmd == ' ':
                self.next_song()
            elif cmd == '-':
                self.drop_song()

    def closing(self):
        print('terminating window')
        self.quit = True
        aidband.stop()
        self.master.destroy()

root = tk.Tk()
app = App(master=root)
app.mainloop()
