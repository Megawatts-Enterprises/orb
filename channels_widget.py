from kivy.properties import ObjectProperty
from kivy.uix.scatter import Scatter
from channel_widget import ChannelWidget
from traceback import print_exc
from kivy.graphics.transformation import Matrix

from htlcs_thread import HTLCsThread
from channels_thread import ChannelsThread
from CN_widget import CNWidget
from node import Node
import data_manager


class ChannelsWidget(Scatter):
    attribute_editor = ObjectProperty(None)

    def __init__(self, *args, **kwargs):
        super(ChannelsWidget, self).__init__(*args, **kwargs)

        self.htlcs_thread = HTLCsThread(inst=self)
        self.htlcs_thread.daemon = True
        self.htlcs_thread.start()

        self.channels_thread = ChannelsThread(inst=self)
        self.channels_thread.daemon = True
        self.channels_thread.start()

        self.cn = []
        self.channels = []
        self.radius = 600
        self.node = None
        lnd = data_manager.data_man.lnd
        try:
            self.channels = sorted(
                lnd.get_channels(),
                key=lambda x: int(x.local_balance) / int(x.capacity),
                reverse=True,
            )
            if not self.channels:
                return
            self.info = lnd.get_info()
            max_cap = max([int(c.capacity) for c in self.channels])
            caps = {
                c.chan_id: max(2, int(int(c.capacity) / max_cap) * 5)
                for c in self.channels
            }
            for i, c in enumerate(self.channels):
                self.cn.append(
                    CNWidget(c=c, caps=caps, attribute_editor=self.attribute_editor)
                )
                self.ids.relative_layout.add_widget(self.cn[-1])
            self.node = Node(
                text=self.info.alias, attribute_editor=self.attribute_editor
            )
            self.ids.relative_layout.add_widget(self.node)
            self.bind(pos=self.update_rect, size=self.update_rect)
        except:
            print_exc()
            print("Issue getting channels")

    def update_rect(self, *args):
        if self.node:
            self.node.pos = (-(70 / 2), -(100 / 2))
        for i in range(len(self.channels)):
            self.cn[i].update_rect(i, len(self.channels))

    def on_touch_down(self, touch):
        if touch.is_mouse_scrolling:
            delta = 0.2
            s = dict(scrolldown=1 + delta, scrollup=1 - delta).get(touch.button)
            if s:
                self.apply_transform(Matrix().scale(s, s, s), anchor=touch.pos)
        else:
            if self.node:
                self.node.col = [80 / 255, 80 / 255, 80 / 255, 1]
            for cn in self.cn:
                cn.b.col = [80 / 255, 80 / 255, 80 / 255, 1]
        super(ChannelsWidget, self).on_touch_down(touch)
