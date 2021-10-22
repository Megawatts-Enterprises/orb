from kivy.clock import mainthread
from kivy.uix.actionbar import ActionButton
from kivy.uix.actionbar import ActionGroup
from kivy.app import App
from kivy_garden.contextmenu import ContextMenuTextItem
from kivy_garden.contextmenu import ContextMenu
from kivy_garden.contextmenu import AppMenuTextItem
from threading import Lock

import data_manager

mutex = Lock()

def console_output(text):
    mutex.acquire()
    try:
	    app = App.get_running_app()
	    console = app.root.ids.sm.get_screen("console")
	    console.print(text)
    finally:
        mutex.release()
