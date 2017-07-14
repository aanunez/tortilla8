#!/usr/bin/env python3

from . import Guacamole
from pygame.locals import *
from os import environ
from tkinter import *
import pygame

class Nacho(Frame):

    WAIT_TIME = 50
    Y_SIZE = 32
    X_SIZE = 64

    def __init__(self):

        # Defaults
        self.foreground_color = (255,255,255)
        self.background_color = (0,0,0)
        self.scale = 18
        self.tile_size = (self.scale, self.scale)
        self.emu = None
        # root, screen, img

        # Init tk
        self.root = Tk()
        Frame.__init__(self, self.root)
        embed = Frame(self.root, width=Game.X_SIZE*self.scale, height=Game.Y_SIZE*self.scale)
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
        setmenu = Menu(menubar, tearoff=0)
        setmenu.add_command(label="Palette", command=self.donothing)
        setmenu.add_command(label="Emulation", command=self.donothing)
        setmenu.add_command(label="Audio", command=self.donothing)
        menubar.add_cascade(label="Settings", menu=setmenu)

        # Populate the 'Help' section
        helpmenu = Menu(menubar, tearoff=0)
        helpmenu.add_command(label="PyPi Index", command=self.donothing)
        helpmenu.add_command(label="Source Code", command=self.donothing)
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
        self.screen = pygame.display.set_mode((Game.X_SIZE*self.scale, Game.Y_SIZE*self.scale));
        self.screen.fill( self.background_color )
        pygame.display.update()



