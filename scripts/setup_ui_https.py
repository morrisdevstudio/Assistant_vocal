"""Prépare l'autorité locale et le certificat UI, sans installer de confiance système."""
import argparse
import datetime as dt
import ipaddress
from pathlib import Path

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import ExtendedKeyUsageOID, NameOID


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--host', type=ipaddress.IPv4Address, help='Adresse IPv4 du PC sur le LAN')
    args = parser.parse_args()
    names = [x509.DNSName('localhost'), x509.IPAddress(ipaddress.ip_address('127.0.0.1'))]
    if args.host and not args.host.is_loopback:
        names.append(x509.IPAddress(args.host))
    root = Path(__file__).resolve().parents[1]
    folder = root / '.local' / 'https'
    folder.mkdir(parents=True, exist_ok=True)
    now = dt.datetime.now(dt.timezone.utc)
    ca_path, ca_key_path = folder / 'ui-ca.crt', folder / 'ui-ca.key'
    if ca_path.exists() != ca_key_path.exists():
        raise RuntimeError('Autorité locale incomplète ; ne pas écraser les fichiers existants.')
    if not ca_path.exists():
        ca_key = rsa.generate_private_key(public_exponent=65537, key_size=3072)
        name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, 'Alfred UI - Autorite locale')])
        ca = (x509.CertificateBuilder().subject_name(name).issuer_name(name)
              .public_key(ca_key.public_key()).serial_number(x509.random_serial_number())
              .not_valid_before(now - dt.timedelta(minutes=5))
              .not_valid_after(now + dt.timedelta(days=1095))
              .add_extension(x509.BasicConstraints(ca=True, path_length=0), critical=True)
              .add_extension(x509.KeyUsage(False, False, False, False, False, True, True, False, False), critical=True)
              .add_extension(x509.SubjectKeyIdentifier.from_public_key(ca_key.public_key()), critical=False)
              .sign(ca_key, hashes.SHA256()))
        ca_key_path.write_bytes(ca_key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()))
        ca_path.write_bytes(ca.public_bytes(serialization.Encoding.PEM))
    else:
        ca = x509.load_pem_x509_certificate(ca_path.read_bytes())
        ca_key = serialization.load_pem_private_key(ca_key_path.read_bytes(), password=None)

    cert_path, key_path = folder / 'ui-server.crt', folder / 'ui-server.key'
    if cert_path.exists() != key_path.exists():
        raise RuntimeError('Certificat UI incomplet ; vérifier les fichiers existants.')
    if not cert_path.exists():
        key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        subject = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, 'Alfred UI LAN')])
        cert = (x509.CertificateBuilder().subject_name(subject).issuer_name(ca.subject)
                .public_key(key.public_key()).serial_number(x509.random_serial_number())
                .not_valid_before(now - dt.timedelta(minutes=5))
                .not_valid_after(now + dt.timedelta(days=365))
                .add_extension(x509.SubjectAlternativeName(names), critical=False)
                .add_extension(x509.BasicConstraints(ca=False, path_length=None), critical=True)
                .add_extension(x509.KeyUsage(True, False, True, False, False, False, False, False, False), critical=True)
                .add_extension(x509.ExtendedKeyUsage([ExtendedKeyUsageOID.SERVER_AUTH]), critical=False)
                .add_extension(x509.AuthorityKeyIdentifier.from_issuer_public_key(ca_key.public_key()), critical=False)
                .sign(ca_key, hashes.SHA256()))
        key_path.write_bytes(key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()))
        cert_path.write_bytes(cert.public_bytes(serialization.Encoding.PEM))

    public_path = root / 'ui' / 'public' / 'alfred-local-ca.crt'
    public_path.parent.mkdir(parents=True, exist_ok=True)
    public_path.write_bytes(ca_path.read_bytes())
    print('Certificat UI et autorité publique préparés. Aucune confiance système installée.')
    print('Empreinte SHA256 de l’autorité :', ca.fingerprint(hashes.SHA256()).hex(':'))


if __name__ == '__main__':
    main()
