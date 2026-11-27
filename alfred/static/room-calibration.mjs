const phrases = [
  { id: "ampli", text: "Alfred, baisse un peu le volume de l’ampli du salon." },
  { id: "enceinte", text: "Alfred, baisse un peu le son de l’enceinte du salon." },
];

const placements = [
  { id: "50cm-face", label: "À 50 cm, de face", instruction: "Placez-vous à 50 cm de l’ESP32, face à lui. Parlez à voix normale." },
  { id: "canape-face", label: "Canapé, de face", instruction: "Asseyez-vous à votre place habituelle et dirigez votre voix vers l’ESP32." },
  { id: "canape-cote", label: "Canapé, de côté", instruction: "Depuis la même place, tournez la tête de 90° par rapport à l’ESP32." },
  { id: "canape-dos", label: "Canapé, de dos", instruction: "Depuis la même place, orientez-vous à l’opposé de l’ESP32. Gardez le même volume de voix." },
];

export const trials = [
  ...[1, 2].map(repeat => ({
    id: `canape-balayage-${repeat}`,
    title: `Balayage au canapé (${repeat}/2)`,
    instruction: "Tenez le téléphone à hauteur de bouche, haut-parleur vers l’ESP32, au volume d’une voix. Gardez-le immobile pendant la lecture.",
  })),
  ...placements.flatMap(place => phrases.map(phrase => ({
    id: `${place.id}-${phrase.id}`,
    title: place.label,
    instruction: place.instruction,
    phrase: phrase.text,
  }))),
];

export function fileName(index) {
  return `${String(index + 1).padStart(2, "0")}-${trials[index].id}.wav`;
}

const utf8 = new TextEncoder();

function crc32(bytes) {
  let crc = -1;
  for (const byte of bytes) {
    crc ^= byte;
    for (let bit = 0; bit < 8; bit++) {
      crc = (crc >>> 1) ^ (0xEDB88320 & -(crc & 1));
    }
  }
  return (crc ^ -1) >>> 0;
}

// ZIP sans compression. Les prises restent dans le navigateur.
function zip(entries) {
  const local = [];
  const directory = [];
  let offset = 0;
  let directorySize = 0;
  for (const { name, data } of entries) {
    const filename = utf8.encode(name);
    const checksum = crc32(data);
    const header = new DataView(new ArrayBuffer(30));
    header.setUint32(0, 0x04034b50, true);
    header.setUint16(4, 20, true);
    header.setUint16(12, 33, true); // 1980-01-01, date minimale du format ZIP.
    header.setUint32(14, checksum, true);
    header.setUint32(18, data.length, true);
    header.setUint32(22, data.length, true);
    header.setUint16(26, filename.length, true);
    local.push(header.buffer, filename, data);

    const entry = new DataView(new ArrayBuffer(46));
    entry.setUint32(0, 0x02014b50, true);
    entry.setUint16(4, 20, true);
    new Uint8Array(entry.buffer).set(new Uint8Array(header.buffer, 4, 26), 6);
    entry.setUint32(42, offset, true);
    directory.push(entry.buffer, filename);
    offset += header.byteLength + filename.length + data.length;
    directorySize += entry.byteLength + filename.length;
  }
  const end = new DataView(new ArrayBuffer(22));
  end.setUint32(0, 0x06054b50, true);
  end.setUint16(8, entries.length, true);
  end.setUint16(10, entries.length, true);
  end.setUint32(12, directorySize, true);
  end.setUint32(16, offset, true);
  return new Blob([...local, ...directory, end.buffer], { type: "application/zip" });
}

export function archive(takes, distance, started) {
  const manifest = {
    emplacement: "salon",
    debut: started.toISOString(),
    distance_canape_m: distance,
    essais: takes.map(({ index }) => ({
      fichier: fileName(index),
      condition: trials[index].id,
      phrase_attendue: trials[index].phrase ?? null,
    })),
  };
  return zip([
    ...takes.map(({ index, data }) => ({ name: fileName(index), data })),
    { name: "parcours.json", data: utf8.encode(JSON.stringify(manifest, null, 2)) },
  ]);
}
