import threading

from kivy.clock import mainthread
from kivy.metrics import dp
from kivymd.uix.tab import MDTabsBase
from kivymd.uix.floatlayout import MDFloatLayout
from kivymd.uix.datatables import MDDataTable

from orb.components.popup_drop_shadow import PopupDropShadow
from orb.misc.ui_actions import console_output
from orb.misc.decorators import guarded
from orb.misc import mempool


class Tab(MDFloatLayout, MDTabsBase):
    """Class implementing content for a tab."""


class BatchOpenScreen(PopupDropShadow):
    @guarded
    def open(self, *args):
        from data_manager import data_man

        self.ids.pubkeys.text = data_man.store.get("batch_open", {}).get("text", "")
        super(BatchOpenScreen, self).open(*args)

    @guarded
    def calculate(self, text, amount):
        from data_manager import data_man

        pks, amounts = [], []
        for line in text.split("\n"):
            if "," in line:
                pk, a = [x.strip() for x in line.split(",")]
                pks.append(pk)
                amounts.append(a)
            else:
                pk = line.strip()
                if pk:
                    pks.append(pk)
        amounts = [int(int(amount) / len(pks)) for _ in range(len(pks))]
        self.ids.pubkeys.text = "\n".join([f"{p},{a}" for p, a in zip(pks, amounts)])

    def ingest(self, text):
        from data_manager import data_man

        data_man.store.put("batch_open", text=text)

    @guarded
    def get_pks_amounts(self):
        pks, amounts = [], []
        for line in self.ids.pubkeys.text.split("\n"):
            if "," in line:
                pk, a = [x.strip() for x in line.split(",")]
                pks.append(pk)
                amounts.append(a)
        return pks, amounts

    @guarded
    def on_tab_switch(self, instance_tabs, instance_tab, instance_tab_label, tab_text):
        if tab_text == "confirm":
            from data_manager import data_man

            pks, amounts = self.get_pks_amounts()
            aliases = [data_man.lnd.get_node_alias(pk) for pk in pks]
            self.ids.table_layout.clear_widgets()
            self.ids.table_layout.add_widget(
                MDDataTable(
                    use_pagination=False,
                    check=False,
                    column_data=[("Alias", dp(60)), ("Amount", dp(30))],
                    row_data=[(al, f"{int(am):,}") for al, am in zip(aliases, amounts)],
                    elevation=2,
                )
            )

    @guarded
    def batch_open(self):
        pks, amounts = self.get_pks_amounts()
        from data_manager import data_man

        try:
            response = data_man.lnd.batch_open(
                pubkeys=pks,
                amounts=amounts,
                sat_per_vbyte=mempool.get_fees("fastestFee") + 1,
            )
            self.ids.open_status.text = str(response)
            console_output(str(response))
        except Exception as e:
            self.ids.open_status.text = e.args[0].details
            console_output(e.args[0].details)

    @guarded
    def batch_connect(self):
        pks, amounts = self.get_pks_amounts()
        from data_manager import data_man

        self.ids.connect.text = ""

        @mainthread
        def print(x):
            self.ids.connect.text += str(x) + "\n"

        def func(*args):
            for pk, amount in zip(pks, amounts):
                info = data_man.lnd.get_node_info(pk)
                print("-" * 50)
                print(data_man.lnd.get_node_alias(pk))
                print("-" * 50)
                for address in info.node.addresses:
                    print(f"Connecting to: {pk}@{address.addr}")
                    try:
                        data_man.lnd.connect(f"{pk}@{address.addr}")
                        print("Success.")
                    except Exception as e:
                        print(e.args[0].details)

        threading.Thread(target=func).start()
