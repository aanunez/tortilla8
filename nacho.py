#!/usr/bin/python3

import os
from kivy.app import App
from kivy.factory import Factory
from kivy.uix.popup import Popup
from kivy.uix.button import Button
from kivy.core.window import Window
from kivy.properties import ObjectProperty
from kivy.uix.floatlayout import FloatLayout
from tortilla8.guacamole import guacamole, Emulation_Error

class LoadDialog(FloatLayout):
    load = ObjectProperty(None)
    cancel = ObjectProperty(None)

class Root(FloatLayout):
    loadfile = ObjectProperty(None)

    def __init__(self, **kwargs):
        super(Root, self).__init__(**kwargs)
        self._keyboard = Window.request_keyboard(self._keyboard_closed, self)
        self._keyboard.bind(on_key_down=self._on_keyboard_down)
        Window.size = (640, 320)
        Window.clearcolor = (1,1,1,1)
        self.emu = None

    def _keyboard_closed(self):
        self._keyboard.unbind(on_key_down=self._on_keyboard_down)
        self._keyboard = None

    def _on_keyboard_down(self, keyboard, keycode, text, modifiers):
        if keycode[1] == 'l':
            self.show_load()
        if keycode[1] == 'c':
            self.ids.game_grid.clear_widgets()
        if keycode[1] == 'p':
            for i in range(64*32):
                if i % 2 == 0:
                    self.ids.game_grid.add_widget(Button(background_color=[1,1,1,1]))
                else:
                    self.ids.game_grid.add_widget(Button(background_color=[0,0,0,1]))
        return True

    def show_load(self):
        content = LoadDialog(load=self.load, cancel=self.dismiss_popup)
        self._popup = Popup(title="Load ROM", content=content, size_hint=(0.9, 0.9))
        self._popup.open()

    def load(self, path, filename):
        self.dismiss_popup()
        try:
            self.emu = guacamole(os.path.join(path, filename[0]), 60)
        except:
            pass

    def dismiss_popup(self):
        self._popup.dismiss()

class nacho(App):
    pass

Factory.register('Root', cls=Root)
nacho().run()
