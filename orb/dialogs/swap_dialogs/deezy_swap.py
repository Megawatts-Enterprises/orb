# -*- coding: utf-8 -*-
# @Author: lnorb.com
# @Date:   2022-01-01 10:03:46
# @Last Modified by:   lnorb.com
# @Last Modified time: 2022-07-27 08:57:46

import threading
from time import sleep
from random import choice
from traceback import format_exc
from functools import lru_cache

import arrow

from kivy.clock import mainthread
from kivy.app import App

from orb.logic.channel_selector import get_low_inbound_channel
from orb.components.popup_drop_shadow import PopupDropShadow
from orb.logic.pay_logic import pay_thread, PaymentStatus
from orb.logic.thread_manager import thread_manager
from orb.misc import data_manager
from orb.lnd import Lnd


chan_ignore = set([])
lock = threading.Lock()
invoices_lock = threading.Lock()


class PaymentUIOption:
    auto_first_hop = 0
    user_selected_first_hop = 1


class DeezySwapDialog(PopupDropShadow):
    def __init__(self, **kwargs):
        self.in_flight = set([])
        PopupDropShadow.__init__(self, **kwargs)
        lnd = Lnd()
        self.chan_id = None
        self.inflight = set([])
        self.inflight_times = {}

        channels = data_manager.data_man.channels

        def timeout_inflight_invoices(self):
            with invoices_lock:
                remove_from_inflight = set([])
                for inv in self.inflight:
                    if arrow.now().timestamp() - self.inflight_times[inv] > 60:
                        remove_from_inflight.add(inv)
                self.inflight -= remove_from_inflight

        @mainthread
        def delayed(chans_pk):
            self.ids.spinner_id.values = chans_pk

        def func():
            chans_pk = [
                f"{c.chan_id}: {lnd.get_node_alias(c.remote_pubkey)}" for c in channels
            ]
            delayed(chans_pk)

        threading.Thread(target=func).start()

    def first_hop_spinner_click(self, chan):
        self.chan_id = int(chan.split(":")[0])

    def load(self):
        from orb.store import model

        invoices = (
            model.Invoice()
            .select()
            .where(model.Invoice.expired() == False, model.Invoice.paid == False)
        )
        return invoices

    def get_ignored_chan_ids(self):
        return set(
            [
                int(k)
                for k, v in App.get_running_app()
                .store.get("pay_through_channel", {})
                .items()
                if not v
            ]
        )

    def pay(self):
        class PayThread(threading.Thread):
            def __init__(self, inst, name, thread_n, *args, **kwargs):
                super(PayThread, self).__init__(*args, **kwargs)
                self._stop_event = threading.Event()
                self.name = str(thread_n)
                self.inst = inst
                self.thread_n = thread_n
                thread_manager.add_thread(self)

            def sprint(self, *args):
                print(f'PT{self.thread_n}: {" ".join(args)}')

            def run(self):
                self.sprint("Running payment thread")
                try:
                    self.__run()
                except:
                    self.sprint("exception in payment thread")
                    print(format_exc())
                finally:
                    self.sprint("stopping payment thread in finally")
                    self.stop()

            def __run(self):
                payment_opt = (
                    PaymentUIOption.user_selected_first_hop
                    if self.inst.chan_id
                    else PaymentUIOption.auto_first_hop
                )
                auto = payment_opt == PaymentUIOption.auto_first_hop

                while not self.stopped():
                    with invoices_lock:
                        all_invoices = self.inst.load()
                        usable_invoices = list(set(all_invoices) - self.inst.inflight)
                        invoice = choice(usable_invoices) if usable_invoices else None
                        if invoice:
                            self.inst.inflight_times[invoice] = arrow.now().timestamp()
                            self.inst.inflight.add(invoice)
                    if invoice:
                        payment_request = Lnd().decode_request(invoice.raw)
                    else:
                        if not all_invoices:
                            self.sprint("no more usable invoices")
                            self.sprint(f"THREAD {self.thread_n} EXITING")
                            return
                        elif not usable_invoices:
                            self.sprint("all invoices are in-flight, sleeping")
                            sleep(30)
                            continue
                    if not auto:
                        chan_id = self.inst.chan_id
                    else:
                        with lock:
                            chan_id = get_low_inbound_channel(
                                lnd=Lnd(),
                                pk_ignore=[],
                                chan_ignore=chan_ignore
                                | self.inst.get_ignored_chan_ids(),
                                num_sats=int(payment_request.num_satoshis)
                                + int(payment_request.num_satoshis)
                                * 0.05,  # 5% for the fees
                            )
                            if chan_id:
                                chan_ignore.add(chan_id)
                    if not chan_id:
                        self.sprint("no more channels left to rebalance")
                        sleep(60)
                    if chan_id:
                        try:
                            status = pay_thread(
                                stopped=self.stopped,
                                thread_n=self.thread_n,
                                fee_rate=int(self.inst.ids.fee_rate.text),
                                payment_request=payment_request,
                                time_pref=float(self.inst.ids.time_pref.value),
                                outgoing_chan_id=chan_id,
                                last_hop_pubkey=None,
                                max_paths=int(self.inst.ids.max_paths.text),
                                payment_request_raw=invoice.raw,
                            )
                        except:
                            self.sprint("Exception in pay_thread")
                            print(format_exc())
                            status = PaymentStatus.exception

                        if chan_id in chan_ignore:
                            with lock:
                                chan_ignore.remove(chan_id)
                        if status == PaymentStatus.inflight:
                            pass
                        elif status in [
                            PaymentStatus.success,
                            PaymentStatus.already_paid,
                        ]:
                            with invoices_lock:
                                invoice.paid = True
                                invoice.save()
                                self.inst.inflight.remove(invoice)
                        elif (
                            status == PaymentStatus.no_routes
                            or status == PaymentStatus.max_paths_exceeded
                        ):
                            if status == PaymentStatus.no_routes:
                                self.sprint("no routes found")
                            if status == PaymentStatus.max_paths_exceeded:
                                self.sprint("max paths exceeded")
                            with invoices_lock:
                                self.inst.inflight.remove(invoice)
                        else:
                            with invoices_lock:
                                self.inst.inflight.remove(invoice)

                    if not auto:
                        break

                    sleep(5)

            def stop(self):
                self._stop_event.set()

            def stopped(self):
                return self._stop_event.is_set()

        for i in range(int(self.ids.num_threads.text)):
            self.thread = PayThread(inst=self, name="PayThread", thread_n=i)
            self.thread.daemon = True
            self.thread.start()

    def kill(self):
        self.thread.stop()
