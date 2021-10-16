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
    config.add_section("debug")
    config.set("debug", "layouts", 0)
    config.set("debug", "blah", 0)
