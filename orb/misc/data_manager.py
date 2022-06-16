# -*- coding: utf-8 -*-
# @Author: lnorb.com
# @Date:   2021-12-01 08:23:35
# @Last Modified by:   lnorb.com
# @Last Modified time: 2022-06-15 02:23:56

from traceback import print_exc

from kivy.storage.jsonstore import JsonStore
from kivy.properties import BooleanProperty
from kivy.properties import NumericProperty
from kivy.properties import StringProperty
from kivy.event import EventDispatcher

from orb.store.db_meta import *
from orb.misc.channels import Channels
from orb.lnd.lnd import Lnd
from orb.misc.utils import pref
from orb.misc.prefs import cert_path
from orb.misc.certificate_secure import CertificateSecure


class DataManager(EventDispatcher):
    """
    The DataManager class is a bit of an unfortunate
    singleton. There's a bunch of data we need to access
    from all over the application.

    It would be better for it not to be singleton, as
    that makes testing difficult, allegidly.
    """

    pubkey = StringProperty("")
    show_chords = BooleanProperty(False)
    menu_visible = BooleanProperty(False)
    show_chord = NumericProperty(0)
    chords_direction = NumericProperty(0)
    channels_widget_ux_mode = NumericProperty(0)
    highlighter_updated = NumericProperty(0)

    def __init__(self, *args, **kwargs):
        """
        DataManager class initializer.
        """
        super(DataManager, self).__init__(*args, **kwargs)
        self.menu_visible = False
        self.disable_shortcuts = False
        self.save_cert()
        self.lnd = Lnd()
        try:
            self.pubkey = self.lnd.get_info().identity_pubkey
        except:
            print_exc()
            print("Error getting pubkey")

        self.plugin_registry = {}

        self.channels = Channels(self.lnd)

        user_data_dir = App.get_running_app().user_data_dir
        self.store = JsonStore(Path(user_data_dir) / pref("path.json") / "orb.json")
        from orb.store import db_create_tables

        for db in [
            forwarding_events_db_name,
            aliases_db_name,
            invoices_db_name,
            htlcs_db_name,
            channel_stats_db_name,
            payments_db_name,
        ]:
            try:
                get_db(db).connect()
            except:
                # most likely already connected
                pass

        db_create_tables.create_forwarding_tables()
        db_create_tables.create_aliases_tables()
        db_create_tables.create_invoices_tables()
        db_create_tables.create_htlcs_tables()
        db_create_tables.create_channel_stats_tables()
        db_create_tables.create_payments_tables()
        db_create_tables.create_path_finding_tables()

    def save_cert(self):
        """
        Save the certificate to an file. This is required for
        requests over rest.
        """
        cert = pref("lnd.tls_certificate")
        if cert:
            with open(cert_path().as_posix(), "w") as f:
                cert_secure = CertificateSecure.init_from_encrypted(cert.encode())
                cert = cert_secure.as_plain_certificate()
                f.write(cert.cert)
        else:
            if cert_path().is_file():
                print("Deleting TLS cert")
                os.unlink(cert_path().as_posix())


data_man = None
