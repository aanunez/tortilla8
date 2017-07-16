#!/usr/bin/env python3

from . import Guacamole, EmulationError
from pygame.locals import *
from os import environ
from tkinter import filedialog
from tkinter import *
import webbrowser
from array import array

# TODO settings menu
# Display Settings
    # Scale edit
    # Unlock aspect ratio or w/e
    # Outline Color
    # Fill Color
    # Background Color
# Emulation Settings
    # Control Edit
    # CPU Freq edit
    # various handles for weird "features"
# Audio
    # Choose freq
    # Custom file

# TODO Help Menu
# About
# PyPi link

# TODO File
# Save/ Saveas

# TODO better error display
# TODO ocationally crashes on windows for no damn reason (fixed?)
# TODO SOUND!

class Nacho(Frame):

    TIMER_REFRESH = 17  # 17ms = 60hz
    INPUT_REFRESH = 200 # 200ms = 5 Hz
    DEFAULT_FREQ = 1000 # Limiting Freq
    Y_SIZE = 32
    X_SIZE = 64

    def __init__(self):

        # Defaults
        self.foreground_color = (255,255,255)
        self.background_color = (0,0,0)
        self.scale = 18
        self.tile_size = (self.scale, self.scale)
        self.emu = None
        self.prev_screen = 0
        self.fatal = False
        self.run_time = 1000 # 1000/this = Freq
        self.controls ={
            48:0x0, 49:0x1, 50:0x2, 51:0x3, # 0 1 2 3
            52:0x4, 53:0x5, 54:0x6, 55:0x7, # 4 5 6 7
            56:0x8, 57:0x9, 47:0xA, 42:0xB, # 8 9 / *
            45:0xC, 43:0xD, 10:0xE, 46:0xF} # - + E .

        # Init tk and canvas
        self.root = Tk()
        self.root.wm_title("Tortilla8 - A Chip8 Emulator")
        self.root.resizable(width=False, height=False)
        Frame.__init__(self, self.root)
        self.menubar = Menu(self.root)
        self.root.config(menu=self.menubar)
        self.root.update()
        self.screen = Canvas(self.root, width=Nacho.X_SIZE*self.scale, height=Nacho.Y_SIZE*self.scale)
        self.screen.create_rectangle( 0, 0, Nacho.X_SIZE*self.scale, Nacho.Y_SIZE*self.scale, fill="black" )
        self.screen.pack()

        # Bind some functions
        self.root.bind("<KeyPress>", self.key_down)
        self.root.bind("<KeyRelease>", self.key_up)
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Populate the 'File' section
        filemenu = Menu(self.menubar, tearoff=0)
        filemenu.add_command(label="Load Rom", command=self.load)
        filemenu.add_command(label="Save", command=self.donothing)
        filemenu.add_command(label="Save as...", command=self.donothing)
        filemenu.add_separator()
        filemenu.add_command(label="Exit", command=self.on_closing)
        self.menubar.add_cascade(label="File", menu=filemenu)

        # Populate the 'Edit' section
        self.antiflicker = BooleanVar()
        self.antiflicker.set(True)
        setmenu = Menu(self.menubar, tearoff=0)
        setmenu.add_command(label="Palette", command=self.donothing)
        setmenu.add_command(label="Emulation", command=self.donothing)
        setmenu.add_command(label="Audio", command=self.donothing)
        setmenu.add_checkbutton(label="Anti-Flicker", onvalue=True, offvalue=False, variable=self.antiflicker)
        self.menubar.add_cascade(label="Settings", menu=setmenu)

        # Populate the 'Help' section
        helpmenu = Menu(self.menubar, tearoff=0)
        helpmenu.add_command(label="PyPi Index", command=self.donothing)
        helpmenu.add_command(label="Source Code", command=lambda:webbrowser.open("https://github.com/aanunez/tortilla8"))
        helpmenu.add_command(label="About", command=self.donothing)
        self.menubar.add_cascade(label="Help", menu=helpmenu)

    def load(self):
        file_path = filedialog.askopenfilename()
        if file_path:
            self.emu = Guacamole(rom=file_path, cpuhz=Nacho.DEFAULT_FREQ, audiohz=60, delayhz=60,
                       init_ram=True, legacy_shift=False, err_unoffical="None",
                       rewind_frames=0)
            self.run_time = 1 # 1khz
            self.emu_event()
            self.timers_event()

    def save(self):
        # Save game state?
        pass

    def donothing(self):
        filewin = Toplevel(self.root)
        button = Button(filewin, text="Do nothing button")
        button.pack()

    def on_closing(self):
        self.root.destroy()

    def key_down(self, key):
        if (len(key.char) != 0) and (self.emu is not None):
            val = self.controls.get(ord(key.char))
            if val:
                self.emu.keypad[val] = True

    def key_up(self, key):
        if (len(key.char) != 0) and (self.emu is not None):
            val = self.controls.get(ord(key.char))
            if val:
                self.emu.keypad[val] = False

    def draw(self):
        self.screen.delete("all")
        self.screen.create_rectangle( 0, 0, Nacho.X_SIZE*self.scale, Nacho.Y_SIZE*self.scale, fill="black" )
        for i,pix in enumerate(self.emu.graphics()):
            if pix:
                x = self.scale*(i%Nacho.X_SIZE)
                y = self.scale*(i//Nacho.X_SIZE)
                self.screen.create_rectangle( x, y, x+self.scale, y+self.scale, fill="white", outline='white' )

    def timers_event(self):
        if (self.emu is not None) and (self.fatal is False):
            if self.emu.sound_timer_register != 0:
                pass #self.sound.play(-1)
            else:
                pass #self.sound.stop()

            self.emu.sound_timer_register -= 1 if self.emu.sound_timer_register != 0 else 0
            self.emu.delay_timer_register -= 1 if self.emu.delay_timer_register != 0 else 0

        self.root.after(Nacho.TIMER_REFRESH, self.timers_event)

    def emu_event(self):
        if self.fatal:
            haltmenu = Menu(self.menubar, tearoff=0)
            self.menubar.add_cascade(label="Fatal Error has occured!", menu=haltmenu)
            # Turn off sound
            return

        self.emu.cpu_tick()

        for err in self.emu.error_log:
            print( str(err[0]) + ": " + err[1] )
            if err[0] is EmulationError._Fatal:
                self.fatal = True
            self.emu.error_log = []

        if self.emu.draw_flag:
            self.emu.draw_flag = False

            if not self.antiflicker.get():
                self.draw()
            else:
                cur_screen = ''
                for i,pix in enumerate(self.emu.graphics()):
                    cur_screen += '1' if pix else '0'
                cur_screen = int(cur_screen,2)

                if ( ( self.prev_screen ^ cur_screen ) & self.prev_screen ) != ( self.prev_screen ^ cur_screen ):
                    self.draw()
                self.prev_screen = cur_screen

        self.root.after(self.run_time, self.emu_event)

if __name__ == "__main__":
    chip8 = Nacho()
    chip8.mainloop()


