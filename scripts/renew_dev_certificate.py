"""Renouvelle le certificat HTTPS de développement local, sans toucher aux services."""
import argparse
import datetime as dt
import ipaddress
import os
from pathlib import Path

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import ExtendedKeyUsageOID, NameOID


def main():
    parser = argparse.ArgumentParser(description="Certificat HTTPS Alfred local")
    parser.add_argument("--directory", type=Path, required=True)
    parser.add_argument("--address", type=ipaddress.IPv4Address, required=True)
    parser.add_argument("--days", type=int, default=365)
    args = parser.parse_args()
    if not 7 <= args.days <= 825:
        parser.error("--days doit être compris entre sept et huit cent vingt-cinq")
    folder = args.directory.resolve()
    folder.mkdir(parents=True, exist_ok=True)
    certificate_path, key_path = folder / "server.crt", folder / "server.key"
    certificate_temp = folder / ".server.crt.new"
    key_temp = folder / ".server.key.new"
    now = dt.datetime.now(dt.timezone.utc)
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "Alfred LAN")])
    certificate = (x509.CertificateBuilder()
        .subject_name(name).issuer_name(name)
        .public_key(key.public_key()).serial_number(x509.random_serial_number())
        .not_valid_before(now - dt.timedelta(minutes=5))
        .not_valid_after(now + dt.timedelta(days=args.days))
        .add_extension(x509.SubjectAlternativeName([
            x509.DNSName("localhost"),
            x509.IPAddress(ipaddress.ip_address("127.0.0.1")),
            x509.IPAddress(args.address)]), critical=False)
        .add_extension(x509.BasicConstraints(ca=False, path_length=None), critical=True)
        .add_extension(x509.ExtendedKeyUsage([ExtendedKeyUsageOID.SERVER_AUTH]), critical=False)
        .sign(key, hashes.SHA256()))
    key_temp.write_bytes(key.private_bytes(
        serialization.Encoding.PEM, serialization.PrivateFormat.TraditionalOpenSSL,
        serialization.NoEncryption()))
    certificate_temp.write_bytes(certificate.public_bytes(serialization.Encoding.PEM))
    os.chmod(key_temp, 0o600)
    os.replace(key_temp, key_path)
    os.replace(certificate_temp, certificate_path)
    print(f"certificat renouvelé jusqu'au {certificate.not_valid_after_utc.isoformat()}")


if __name__ == "__main__":
    main()
