from kivy.clock import Clock
from kivy.clock import mainthread
from kivy.uix.screenmanager import Screen
from channels_widget import *


class ChannelsScreen(Screen):
    def __init__(self, *args, **kwargs):
        super(ChannelsScreen, self).__init__(*args, **kwargs)
        self.channels_widget = None

    def on_enter(self, *args):
        if not self.channels_widget:
            Clock.schedule_once(self.build, 2)

    def build(self, *args):
        @mainthread
        def delayed():
            self.channels_widget = ChannelsWidget(
                attribute_editor=self.ids.attribute_editor
            )
            self.ids.relative_layout.add_widget(self.channels_widget)

        delayed()

    def refresh(self):
        if self.channels_widget:
            self.channels_widget.htlcs_thread.stop()
            self.channels_widget.channels_thread.stop()
            self.ids.relative_layout.clear_widgets()
            self.build()
