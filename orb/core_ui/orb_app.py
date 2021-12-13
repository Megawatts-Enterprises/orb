import os
import sys
from pathlib import Path

from kivymd.app import MDApp
from kivy.lang import Builder
from kivymd.effects import stiffscroll

from orb.misc.monkey_patch import do_monkey_patching
from orb.misc.conf_defaults import set_conf_defaults
from orb.audio.audio_manager import audio_manager
from orb.misc.decorators import guarded
from orb.core_ui.main_layout import MainLayout
from orb.misc.ui_actions import console_output


import data_manager

do_monkey_patching()
is_dev = sys.argv[0] == "main.py"


class OrbApp(MDApp):
    title = "Orb"

    def load_kvs(self):
        for path in [str(x) for x in Path(".").rglob("*.kv")]:
            if any(x in path for x in ["tutes", "dist", "user"]):
                continue
            if is_dev and "orb.kv" in path:
                continue
            Builder.load_file(path)
        if not is_dev:
            Builder.load_file("kivy_garden/contextmenu/app_menu.kv")
            Builder.load_file("kivy_garden/contextmenu/context_menu.kv")

    def load_user_setup(self):
        if os.path.exists("user/scripts/user_setup.py"):
            from importlib import __import__

            try:
                __import__("user.scripts.user_setup")
            except:
                print("Unable to load user_setup.py")

    def on_start(self):
        audio_manager.set_volume()
        self.load_user_setup()

        import sys

        _write = sys.stdout.write

        def write(*args):
            content = " ".join(args)
            _write(content)
            console_output(content)

        sys.stdout.write = write

    def build(self):
        """
        Main build method for the app.
        """
        self.load_kvs()
        data_manager.data_man = data_manager.DataManager(config=self.config)
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = self.config["display"]["primary_palette"]
        self.icon = "orb.png"
        self.main_layout = MainLayout()
        return self.main_layout

    def build_config(self, config):
        """
        Default config values.
        """
        set_conf_defaults(config)

    def build_settings(self, settings):
        """
        Configuration screen for the app.
        """
        settings.add_json_panel("Orb", self.config, filename="orb/misc/settings.json")

    def on_config_change(self, config, section, key, value):
        """
        What to do when a config value changes. TODO: needs fixing.
        Currently we'd end up with multiple LND instances for example?
        Simply not an option.
        """
        if f"{section}.{key}" == "audio.volume":
            audio_manager.set_volume()
        elif key == "tls_certificate":
            data_manager.DataManager.save_cert(value)
        self.main_layout.do_layout()

    @guarded
    def run(self, *args):
        super(OrbApp, self).run(*args)
