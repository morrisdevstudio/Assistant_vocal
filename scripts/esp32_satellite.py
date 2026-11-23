"""Vérification LAN/OTA sans flashage et redémarrage ciblé du satellite Alfred."""
import argparse
import asyncio
import ipaddress
import json
from pathlib import Path
import socket

from aioesphomeapi import APIClient, ButtonInfo

ROOT = Path(__file__).resolve().parents[1]


def receive(sock, size):
    data = bytearray()
    while len(data) < size:
        part = sock.recv(size - len(data))
        if not part:
            raise ValueError("Connexion OTA interrompue")
        data.extend(part)
    return bytes(data)


def check_ota(address):
    # Protocole ESPHome : s'arrêter AVANT l'envoi de la taille du firmware,
    # première étape pouvant préparer/effacer une partition. Aucun binaire envoyé.
    with socket.create_connection((address, 3232), timeout=5) as sock:
        sock.sendall(bytes([0x6C, 0x26, 0xF7, 0x5C, 0x45]))
        reply = receive(sock, 2)
        if reply[0] != 0 or reply[1] not in (1, 2):
            raise ValueError("Protocole OTA non reconnu")
        sock.sendall(b"\x00")
        if receive(sock, 1) != b"\x40":
            raise ValueError("Négociation OTA refusée")
        auth = receive(sock, 1)[0]
        if auth not in (0x01, 0x02, 0x41):
            raise ValueError("Authentification OTA non reconnue")
        return {"version": reply[1], "authentication_required": auth != 0x41,
                "flash_written": False}


async def inspect(config_path, restart=False):
    config = json.loads(config_path.read_text(encoding="utf-8-sig"))
    if config.get("enabled") is not True:
        raise ValueError("Satellite désactivé")
    address = await asyncio.to_thread(socket.gethostbyname, config["host"])
    if not ipaddress.ip_address(address).is_private:
        raise ValueError("Adresse du satellite non locale")
    client = APIClient(address, 6053, None, client_info="Alfred satellite maintenance")
    try:
        await asyncio.wait_for(client.connect(login=True), 10)
        info = await asyncio.wait_for(client.device_info(), 10)
        if info.mac_address.casefold() != config["expected_mac"].casefold():
            raise ValueError("Identité du satellite différente ; opération refusée")
        report = {"host": config["host"], "address": address, "name": info.name,
                  "esphome": info.esphome_version, "project": info.project_name,
                  "firmware": info.project_version, "identity_verified": True}
        if restart:
            entities, _ = await asyncio.wait_for(client.list_entities_services(), 10)
            button = next((e for e in entities if isinstance(e, ButtonInfo)
                           and e.object_id == "restart"), None)
            if button is None:
                raise ValueError("Bouton de redémarrage absent")
            client.button_command(button.key)
            await asyncio.sleep(.5)
            report["restart_requested"] = True
        else:
            report["ota"] = await asyncio.to_thread(check_ota, address)
        return report
    finally:
        await client.disconnect()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=ROOT / ".local/data/terminal.json")
    parser.add_argument("--restart", action="store_true", help="Redémarrer uniquement la carte identifiée")
    args = parser.parse_args()
    try:
        print(json.dumps(asyncio.run(inspect(args.config, args.restart)), ensure_ascii=False, indent=2))
    except (OSError, ValueError, TimeoutError) as error:
        parser.exit(1, f"Vérification impossible : {error}\n")


if __name__ == "__main__":
    main()
