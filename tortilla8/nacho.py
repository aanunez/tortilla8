#!/usr/bin/env python3

from tortilla8 import Guacamole
from pygame.locals import *
from os import environ
from tkinter import filedialog
from tkinter import *
import pygame
import webbrowser

# TODO Preserve aspect ratio, enable resize (hard)
# TODO All gui options - Pall, Emulation, Audio, About, PyPi, Save, Save as
# TODO CPU freq is hard locked to 1khz
# TODO default Audio
# TODO default Keys

class Nacho(Frame):

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
        # root, screen, img

        # Init tk
        self.root = Tk()
        self.root.wm_title("Tortilla8 - A Chip8 Emulator")
        Frame.__init__(self, self.root)
        embed = Frame(self.root, width=Nacho.X_SIZE*self.scale, height=Nacho.Y_SIZE*self.scale)
        embed.pack()
        self.root.resizable(width=False, height=False)

        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Make the tk Menu bar
        menubar = Menu(self.root)

        # Populate the 'File' section
        filemenu = Menu(menubar, tearoff=0)
        filemenu.add_command(label="Load Rom", command=self.load)
        filemenu.add_command(label="Save", command=self.donothing)
        filemenu.add_command(label="Save as...", command=self.donothing)
        filemenu.add_separator()
        filemenu.add_command(label="Exit", command=self.on_closing)
        menubar.add_cascade(label="File", menu=filemenu)

        # Populate the 'Edit' section
        self.antiflicker = BooleanVar()
        self.antiflicker.set(True)
        setmenu = Menu(menubar, tearoff=0)
        setmenu.add_command(label="Palette", command=self.donothing)
        setmenu.add_command(label="Emulation", command=self.donothing)
        setmenu.add_command(label="Audio", command=self.donothing)
        setmenu.add_checkbutton(label="Anti-Flicker", onvalue=True, offvalue=False, variable=self.antiflicker)
        menubar.add_cascade(label="Settings", menu=setmenu)

        # Populate the 'Help' section
        helpmenu = Menu(menubar, tearoff=0)
        helpmenu.add_command(label="PyPi Index", command=self.donothing)
        helpmenu.add_command(label="Source Code", command=lambda:webbrowser.open("https://github.com/aanunez/tortilla8"))
        helpmenu.add_command(label="About", command=self.donothing)
        menubar.add_cascade(label="Help", menu=helpmenu)

        # Add menubar to window, set the rest of the winndow to SDL's output
        self.root.config(menu=menubar)
        environ['SDL_WINDOWID'] = str(embed.winfo_id())
        self.root.update()

        # Init Py Game
        pygame.init()
        self.img = pygame.Surface( self.tile_size );
        self.img.fill( self.foreground_color );
        self.screen = pygame.display.set_mode((Nacho.X_SIZE*self.scale, Nacho.Y_SIZE*self.scale));
        self.screen.fill( self.background_color )
        pygame.display.update()

    def load(self):
        #file_path = filedialog.askopenfilename()
        file_path = '/home/adam/git/tortilla8/exclude/zero.ch8'
        if file_path:
            self.emu = Guacamole(rom=file_path, cpuhz=1000, audiohz=60, delayhz=60,
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
        pygame.quit()
        self.root.quit()
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

    def run(self):
        for event in pygame.event.get():
            if event.type == KEYDOWN:
                print(event.key) # TODO Actually capture keys

        if self.emu is not None:
            self.emu.run()
            self.draw()
            if self.emu.sound_timer_register != 0:
                pass # TODO Play sound

        self.root.after(Nacho.WAIT_TIME, self.run)

if __name__ == "__main__":
    chip8 = Nacho()
    chip8.run()
    chip8.mainloop()

