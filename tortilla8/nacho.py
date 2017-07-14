#!/usr/bin/env python3

from tortilla8 import Guacamole, EmulationError
from pygame.locals import *
from os import environ
from tkinter import filedialog
from tkinter import *
import pygame
import webbrowser
from array import array
from pygame.mixer import Sound, get_init

# TODO Preserve aspect ratio, enable resize (hard)
# TODO All gui options - Pall, Emulation, Audio, About, PyPi, Save, Save as
# TODO CPU freq is hard locked to 1khz
# TODO default Keys
# TODO better error display

class Nacho(Frame):

    DEFAULT_FREQ = 1000 # Limited
    WAIT_TIME = 1 # Limits emu freq.
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
        # root, screen, img, sound

        # Init tk
        self.root = Tk()
        self.root.wm_title("Tortilla8 - A Chip8 Emulator")
        Frame.__init__(self, self.root)
        embed = Frame(self.root, width=Nacho.X_SIZE*self.scale, height=Nacho.Y_SIZE*self.scale)
        embed.pack()
        self.root.resizable(width=False, height=False)

        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Make the tk Menu bar
        self.menubar = Menu(self.root)

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

        # Add self.menubar to window, set the rest of the winndow to SDL's output
        self.root.config(menu=self.menubar)
        environ['SDL_WINDOWID'] = str(embed.winfo_id())
        self.root.update()

        # Init Py Game
        pygame.init()
        self.img = pygame.Surface( self.tile_size );
        self.img.fill( self.foreground_color );
        self.screen = pygame.display.set_mode((Nacho.X_SIZE*self.scale, Nacho.Y_SIZE*self.scale));
        self.screen.fill( self.background_color )
        pygame.display.update()
        self.sound = Note(440)

    def load(self):
        file_path = filedialog.askopenfilename()
        if file_path:
            self.emu = Guacamole(rom=file_path, cpuhz=DEFAULT_FREQ, audiohz=60, delayhz=60,
                       init_ram=True, legacy_shift=False, err_unoffical="None",
                       rewind_depth=0)

    def save(self):
        # Save game state?
        pass

    def donothing(self):
        filewin = Toplevel(self.root)
        button = Button(filewin, text="Do nothing button")
        button.pack()

    def on_closing(self):
        #pygame.quit() Both of these waste too much time.
        #self.root.quit()
        self.root.destroy()

    def draw(self):
        if not self.emu.draw_flag:
            return
        self.emu.draw_flag = False

        if self.antiflicker.get():
            cur_screen = ''
            for i,pix in enumerate(self.emu.graphics()):
                cur_screen += '1' if pix else '0'
            cur_screen = int(cur_screen,2)

            if ( ( self.prev_screen ^ cur_screen ) & self.prev_screen ) != ( self.prev_screen ^ cur_screen ):
                self._draw()

            self.prev_screen = cur_screen

        else:
            self._draw()

        pygame.display.update()

    def _draw(self):
        self.screen.fill( self.background_color )
        for i,pix in enumerate(self.emu.graphics()):
            if pix:
                self.screen.blit(self.img, ( self.scale*(i%Nacho.X_SIZE), self.scale*(i//Nacho.X_SIZE) ) )

    def halt(self):
        self.fatal = True
        haltmenu = Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="Fatal Error has occured!", menu=haltmenu)
        self.sound.stop()

    def run(self):
        for event in pygame.event.get():
            if event.type == KEYDOWN:
                print(event.key) # TODO Actually capture keys

        if (self.emu is not None) and (self.fatal is False):
            self.emu.run()
            if any(e[0] is EmulationError._Fatal for e in self.emu.error_log):
                self.halt()
            self.draw()
            if self.emu.sound_timer_register != 0:
                self.sound.play(-1)
            else:
                self.sound.stop()

        self.root.after(Nacho.WAIT_TIME, self.run)

class Note(Sound):

    def __init__(self, frequency, volume=.1):
        self.frequency = frequency
        Sound.__init__(self, self.build_samples())
        self.set_volume(volume)

    def build_samples(self):
        period = int(round(get_init()[0] / self.frequency))
        samples = array("h", [0] * period)
        amplitude = 2 ** (abs(get_init()[1]) - 1) - 1
        for time in range(period):
            if time < period / 2:
                samples[time] = amplitude
            else:
                samples[time] = -amplitude
        return samples

if __name__ == "__main__":
    chip8 = Nacho()
    chip8.run()
    chip8.mainloop()

