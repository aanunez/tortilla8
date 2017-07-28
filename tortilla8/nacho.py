#!/usr/bin/env python3

from . import Guacamole, EmulationError
from os import environ
from os.path import join as pathjoin
from tkinter import *
from tkinter import filedialog
from webbrowser import open as openweb
from array import array

# Import Sound (optional)
try: import simpleaudio as sa
except ImportError:
    sa = None

# TODO Settings windows below
# TODO better error display.
#    Display error?
#    Doesn't remove itself after error

class Nacho(Frame):

    TIMER_REFRESH = 17  # 17ms = 60hz
    INPUT_REFRESH = 200 # 200ms = 5 Hz
    DEFAULT_FREQ = 1000 # Limiting Freq
    Y_SIZE = 32
    X_SIZE = 64
    ABOUT ='''
           Tortilla8 is a collection of Chip8 tools tools for per-processing,
           assembling, emulating, disassembling, and visualizing Chip8 ROMs
           written by Adam Nunez. This software is free, like free speach,
           and is licensed under the GPLv3. Feel free to share this program,
           make modifications, or suggest fixes via github.
           '''

    def __init__(self):

        # Defaults
        self.scale = 18
        self.tile_size = (self.scale, self.scale)
        self.emu = None
        self.prev_screen = 0
        self.fatal = False
        self.run_time = 1000 # 1000/this = Freq
        self.color_border = "white"
        self.color_fill = "white"
        self.color_back = "black"
        self.controls ={
            'KP_0':0x0, 'KP_1':0x1, 'KP_2':0x2, 'KP_3':0x3,
            'KP_4':0x4, 'KP_5':0x5, 'KP_6':0x6, 'KP_7':0x7,
            'KP_8':0x8, 'KP_9':0x9, 'KP_Divide':0xA, 'KP_Multiply':0xB,
            'KP_Subtract':0xC, 'KP_Add':0xD, 'KP_Enter':0xE, 'KP_Decimal':0xF}

        # Setup audio
        self.wave_file = pathjoin('tortilla8','sound','play.wav')
        self.audio_on = False
        if sa is None:
            print("SimpleAudio is missing from your system. You can install it " + \
                "via 'pip install simpleaudio'. Audio has been disabled.")
        else:
            try:
                self.wave_obj = sa.WaveObject.from_wave_file(self.wave_file)
                self.play_obj = None
                self.audio_playing = False
                self.audio_on = True
            except FileNotFoundError:
                print("An error occured while initalizing audo. Audio has been disabled.")

        # Init TK and canvas
        self.root = Tk()
        self.root.wm_title("Tortilla8 - A Chip8 Emulator")
        self.root.resizable(width=False, height=False)
        Frame.__init__(self, self.root)
        self.menubar = Menu(self.root)
        self.root.config(menu=self.menubar)
        self.root.update()
        self.screen = Canvas(self.root, width=Nacho.X_SIZE*self.scale, height=Nacho.Y_SIZE*self.scale)
        self.screen.create_rectangle( 0, 0, Nacho.X_SIZE*self.scale, Nacho.Y_SIZE*self.scale, fill=self.color_back )
        self.screen.pack()

        # Init TK Vars
        self.antiflicker = BooleanVar()
        self.antiflicker.set(True)
        self.lock_aspect = BooleanVar()
        self.lock_aspect.set(True)

        # Bind some functions
        self.root.bind("<KeyPress>", self.key_down)
        self.root.bind("<KeyRelease>", self.key_up)
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Populate the 'File' section
        filemenu = Menu(self.menubar, tearoff=0)
        filemenu.add_command(label="Load Rom", command=self.load)
        filemenu.add_command(label="Exit", command=self.on_closing)
        self.menubar.add_cascade(label="File", menu=filemenu)

        # Populate the 'Settings' section
        setmenu = Menu(self.menubar, tearoff=0)
        setmenu.add_command(label="Display", command=self.win_display_settings)
        setmenu.add_command(label="Emulation", command=self.win_emu_settings)
        if self.audio_on:
            setmenu.add_command(label="Audio", command=self.win_audio_settings)
        else:
            setmenu.add_command(label="Audio", command=self.win_audio_settings, state='disable')
        setmenu.add_checkbutton(label="Anti-Flicker", onvalue=True, offvalue=False, variable=self.antiflicker)
        self.menubar.add_cascade(label="Settings", menu=setmenu)

        # Populate the 'Help' section
        helpmenu = Menu(self.menubar, tearoff=0)
        helpmenu.add_command(label="PyPi Index",
            command=lambda:openweb("https://pypi.org/project/tortilla8"))
        helpmenu.add_command(label="Source Code",
            command=lambda:openweb("https://github.com/aanunez/tortilla8"))
        helpmenu.add_command(label="About", command=self.window_about)
        self.menubar.add_cascade(label="Help", menu=helpmenu)

    def load(self):
        file_path = filedialog.askopenfilename()
        if file_path:
            self.emu = Guacamole(rom=file_path, cpuhz=Nacho.DEFAULT_FREQ, audiohz=60, delayhz=60,
                       init_ram=True, legacy_shift=False, err_unoffical="None", rewind_frames=0)
            self.run_time = 1 # 1khz
            self.emu_event()
            self.timers_event()

    def set_controls(self, *controls):
        tmp = {}
        for i, key in enumerate(controls):
            tmp[key] = i
        self.controls = tmp

    def win_display_settings(self):
        # Display Settings TODO
        # Scale edit
        # Unlock aspect ratio
        # Outline Color
        # Fill Color
        # Background Color
        window = Toplevel(self)
        window.wm_title("Display Settings")
        window.minsize(width=264, height=190)
        window.resizable(width=False, height=False)
        Checkbutton(window, text="Lock Aspect Ratio", variable=self.lock_aspect).place(x=10, y=15)
        Label(window, text="Scale: ").place(x=160, y=16)
        e = Entry(window)
        e.insert(0, str(self.scale))
        e.place(x=210, y=16, width=40)
        Label(window, text="Background").place(x=14, y=65)
        Label(window, text="Foreground").place(x=14, y=105)
        Label(window, text="Border").place(x=14, y=145)

    def win_emu_settings(self):
        # Emulation Settings TODO
        # Controls Edit
        # CPU Freq edit
        # various handles for weird "features"
        window = Toplevel(self)
        window.resizable(width=False, height=False)
        label = Label(window, text="temp")
        label.pack(side="top", fill="both", padx=10, pady=10)

    def win_audio_settings(self):
        # Audio TODO
        # Choose freq
        # Custom file
        # mute?
        window = Toplevel(self)
        window.resizable(width=False, height=False)
        label = Label(window, text="temp")
        label.pack(side="top", fill="both", padx=10, pady=10)

    def window_about(self):
        window = Toplevel(self)
        window.resizable(width=False, height=False)
        label = Label(window, text=' '.join(Nacho.ABOUT.split(' '*11)))
        label.pack(side="top", fill="both", padx=10, pady=10)

    def on_closing(self):
        self.root.destroy()

    def key_down(self, key):
        if self.emu is not None:
            val = self.controls.get(key.keysym)
            if val:
                self.emu.keypad[val] = True

    def key_up(self, key):
        if self.emu is not None:
            val = self.controls.get(key.keysym)
            if val:
                self.emu.keypad[val] = False

    def draw(self):
        self.screen.delete("all")
        self.screen.create_rectangle( 0, 0, Nacho.X_SIZE*self.scale,
            Nacho.Y_SIZE*self.scale, fill=self.color_back )
        for i,pix in enumerate(self.emu.graphics()):
            if pix:
                x = self.scale*(i%Nacho.X_SIZE)
                y = self.scale*(i//Nacho.X_SIZE)
                self.screen.create_rectangle( x, y, x+self.scale, y+self.scale,
                    fill=self.color_fill, outline=self.color_border )

    def timers_event(self):
        if (self.emu is not None) and (self.fatal is False):
            if self.audio_on:
                if self.emu.sound_timer_register != 0:
                    self.wave_obj.play()
                else:
                    sa.stop_all()

            self.emu.sound_timer_register -= 1 if self.emu.sound_timer_register != 0 else 0
            self.emu.delay_timer_register -= 1 if self.emu.delay_timer_register != 0 else 0

        self.root.after(Nacho.TIMER_REFRESH, self.timers_event)

    def emu_event(self):
        if self.fatal:
            haltmenu = Menu(self.menubar, tearoff=0)
            self.menubar.add_cascade(label="Fatal Error has occured!", menu=haltmenu)
            if self.audio_on:
                sa.stop_all()
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

