def set_conf_defaults(config):
    config.add_section("lnd")
    config.set("lnd", "hostname", "localhost")
    config.set("lnd", "rest_port", "8080")
    config.set("lnd", "grpc_port", "10009")
    config.set("lnd", "protocol", "mock")
    config.set("lnd", "tls_certificate", "")
    config.set("lnd", "network", "mainnet")
    config.set("lnd", "macaroon_admin", "")
    config.add_section("display")
    config.set("display", "channel_length", 600)
    config.set("display", "show_sent_received", 0)
    config.set("display", "channel_opacity", 0.8)
    config.set("display", "channels_background_color", '(.2, .2, .3, 1)')
    config.set("display", "1m_color", '[100 / 255, 245 / 255, 100 / 255, 1]')
    config.set("display", "node_background_color", '[80 / 255, 80 / 255, 80 / 255, 1]')
    config.set("display", "node_selected_background_color", '[150 / 255, 150 / 255, 150 / 255, 1]')
    config.set("display", "node_width", 70)
    config.set("display", "node_height", 100)
    config.add_section("audio")
    config.set("audio", "volume", 0.2)
    config.add_section("debug")
    config.set("debug", "layouts", 0)
