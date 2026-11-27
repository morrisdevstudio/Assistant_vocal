#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 || $# -gt 3 ]]; then
    echo "Usage : bash deploy/debian/build.sh <révision Git> [dossier de sortie] [révision Debian]" >&2
    exit 2
fi

root=$(git -C "$(dirname "$0")" rev-parse --show-toplevel)
revision=$(git -C "$root" rev-parse --verify --end-of-options "$1^{commit}")
output=${2:-"$root/.local/debian-packages"}
debian_revision=${3:-}
if [[ -n $debian_revision && ! $debian_revision =~ ^[1-9][0-9]*$ ]]; then
    echo "La révision Debian doit être un entier positif." >&2
    exit 2
fi
mkdir -p -- "$output"
output=$(cd -- "$output" && pwd)
work=$(mktemp -d)
trap 'rm -rf -- "$work"' EXIT

python3 - <<'PY'
import platform
import sys

os_info = platform.freedesktop_os_release() if sys.platform == "linux" else {}
if (os_info.get("ID"), os_info.get("VERSION_ID"), platform.machine(), sys.version_info[:2]) != (
    "debian", "13", "x86_64", (3, 13),
):
    sys.exit("Construire le paquet sur Debian 13 amd64 avec Python 3.13.")
PY

source_dir="$work/source"
mkdir -- "$source_dir"
git -C "$root" archive "$revision" alfred native/murmure-stt ui deploy/debian pyproject.toml requirements.lock.txt \
    | tar -x -C "$source_dir"

version=$(cd "$source_dir" && python3 -c 'import tomllib; print(tomllib.load(open("pyproject.toml", "rb"))["project"]["version"])')
[[ $version =~ ^[0-9]+\.[0-9]+\.[0-9]+[A-Za-z0-9.+-]*$ ]]
release="${version}-${revision:0:12}"
name="alfred-${release}-debian13-amd64"
bundle="$work/$name"
mkdir -p -- "$bundle/bin" "$bundle/wheels"
printf '%s\n' "$release" > "$bundle/RELEASE"
cp -a -- "$source_dir/alfred" "$bundle/alfred"
cp -- "$source_dir/deploy/debian/"{install.py,health.py,alfred.service,README.md,runtime.txt} "$bundle/"
cp -- "$source_dir/deploy/debian/"{updater.py,alfred-home-update.path,alfred-home-update.service,alfred-home-auto-update.timer,alfred-home-auto-update.service} "$bundle/"
cp -- "$source_dir/requirements.lock.txt" "$bundle/constraints.txt"
cp -- "$source_dir/native/murmure-stt/"{LICENSE,ONNXRUNTIME-LICENSE,UPSTREAM.json} "$bundle/bin/"

python3 -m venv "$work/build-venv"
"$work/build-venv/bin/python" -m pip download --only-binary=:all: \
    -c "$bundle/constraints.txt" -r "$bundle/runtime.txt" -d "$bundle/wheels"

cargo build --release --locked --manifest-path "$source_dir/native/murmure-stt/Cargo.toml" \
    --target-dir "$work/cargo-target"
install -m 0755 -- "$work/cargo-target/release/alfred-murmure-stt" "$bundle/bin/alfred-murmure-stt"

npm --prefix "$source_dir/ui" ci
# La PWA est servie par Alfred sous /pwa/ : les ressources doivent viser ce préfixe.
ALFRED_UI_BASE=/pwa/ npm --prefix "$source_dir/ui" run build
mv -- "$source_dir/ui/dist" "$bundle/pwa"

tar -czf "$output/$name.tar.gz" -C "$work" -- "$name"
(cd "$output" && sha256sum -- "$name.tar.gz" > "$name.tar.gz.sha256")
printf 'Paquet : %s/%s.tar.gz\n' "$output" "$name"
if [[ -n $debian_revision ]]; then
    bash "$source_dir/deploy/debian/make-deb.sh" "$bundle" "$debian_revision" "$output"
fi
