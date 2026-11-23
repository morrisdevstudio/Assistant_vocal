"""Icônes PNG de l'onde Alfred, générées sans dépendance externe."""
import struct
import zlib
from pathlib import Path


def chunk(kind, data):
    return struct.pack('!I', len(data)) + kind + data + struct.pack('!I', zlib.crc32(kind + data))


def icon(size):
    rows = bytearray()
    # Onde centrée dans la zone sûre d'une icône Android maskable.
    bars = [(0.30, 0.46, 0.54), (0.38, 0.36, 0.64), (0.46, 0.28, 0.72),
            (0.54, 0.39, 0.61), (0.62, 0.33, 0.67), (0.70, 0.44, 0.56)]
    radius = .018
    for y in range(size):
        rows.append(0)
        for x in range(size):
            px, py = (x + .5) / size, (y + .5) / size
            distance = min(((px - bx)**2 + (py - min(max(py, lo), hi))**2)**.5 for bx, lo, hi in bars)
            coverage = max(0, min(1, (radius - distance) * size + .5))
            value = round(33 + (239 - 33) * coverage)
            rows.extend((value, value, value))
    header = struct.pack('!2I5B', size, size, 8, 2, 0, 0, 0)
    return b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', header) + chunk(b'IDAT', zlib.compress(bytes(rows), 9)) + chunk(b'IEND', b'')


if __name__ == '__main__':
    folder = Path(__file__).resolve().parents[1] / 'ui' / 'public' / 'icons'
    folder.mkdir(parents=True, exist_ok=True)
    for size in (192, 512):
        (folder / f'alfred-{size}.png').write_bytes(icon(size))
    (folder / 'alfred-maskable-512.png').write_bytes((folder / 'alfred-512.png').read_bytes())
    print('Trois icônes PNG générées.')
