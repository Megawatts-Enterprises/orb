from orb.components.popup_drop_shadow import PopupDropShadow
from kivy.clock import mainthread

import threading
import data_manager
from orb.misc.output import *
from orb.logic.pay_logic import pay_thread


class Rebalance(PopupDropShadow):
    def __init__(self, **kwargs):
        PopupDropShadow.__init__(self, **kwargs)
        self.output = Output(None)
        self.output.lnd = data_manager.data_man.lnd
        lnd = data_manager.data_man.lnd
        self.chan_id = None
        self.last_hop_pubkey = None
        self.alias_to_pk = {}

        @mainthread
        def delayed():
            channels = lnd.get_channels()
            for c in channels:
                self.ids.spinner_out_id.values.append(
                    f"{c.chan_id}: {lnd.get_node_alias(c.remote_pubkey)}"
                )
                self.ids.spinner_in_id.values.append(
                    f"{lnd.get_node_alias(c.remote_pubkey)}"
                )
                self.alias_to_pk[lnd.get_node_alias(c.remote_pubkey)] = c.remote_pubkey

        delayed()

    def first_hop_spinner_click(self, chan):
        self.chan_id = int(chan.split(":")[0])

    def last_hop_spinner_click(self, alias):
        self.last_hop_pubkey = self.alias_to_pk[alias]

    def rebalance(self):
        def thread_function():
            payment_request = data_manager.data_man.lnd.generate_invoice(
                memo='rebalance', amount=int(self.ids.amount.text)
            )
            status = pay_thread(
                inst=self,
                thread_n=0,
                fee_rate=int(self.ids.fee_rate.text),
                payment_request=payment_request,
                outgoing_chan_id=self.chan_id,
                last_hop_pubkey=self.last_hop_pubkey,
                max_paths=int(self.ids.max_paths.text),
            )

        self.thread = threading.Thread(target=thread_function)
        self.thread.daemon = True
        self.thread.start()

    def kill(self):
        self.thread.stop()
