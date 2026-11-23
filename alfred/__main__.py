"""Serveur de développement : local par défaut, adresse privée explicite en option."""

import argparse
from dataclasses import replace
import ipaddress
import ssl

import uvicorn

from alfred.config import Settings


def private_address(value):
    try:
        address = ipaddress.IPv4Address(value)
        if address.is_loopback or any(address in ipaddress.ip_network(network) for network in (
                "10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16")):
            return str(address)
    except ValueError:
        pass
    raise argparse.ArgumentTypeError("Indiquez une adresse IPv4 locale ou privée du PC.")


def main():
    from alfred.runtime import prefer_interactive_cpu
    prefer_interactive_cpu()
    parser = argparse.ArgumentParser(description="Alfred — prototype local")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--host", type=private_address, default="127.0.0.1",
                        help="Adresse du PC ; exemple LAN/VPN : 192.168.77.23")
    parser.add_argument("--https", action="store_true",
                        help="HTTPS direct avec server.crt et server.key dans .local/https")
    args = parser.parse_args()
    from alfred.app import create_app
    settings = replace(Settings.from_env(), listen_host=args.host)
    tls = {}
    if args.https:
        directory = settings.data_dir.parent / "https"
        certificate, key = directory / "server.crt", directory / "server.key"
        try:
            ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER).load_cert_chain(certificate, key)
        except (OSError, ssl.SSLError):
            parser.error("Certificat HTTPS absent ou invalide : préparer server.crt et server.key dans "
                         + str(directory))
        tls = {"ssl_certfile": str(certificate), "ssl_keyfile": str(key)}
    uvicorn.run(create_app(settings), host=args.host, port=args.port,
                workers=1, access_log=False, **tls)


if __name__ == "__main__":
    main()
