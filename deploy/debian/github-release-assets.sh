#!/usr/bin/env bash
set -euo pipefail
umask 022

if [[ $# != 3 || ! $1 =~ ^([[:xdigit:]]{40}|[[:xdigit:]]{64})$ ]]; then
    echo "Usage : bash github-release-assets.sh <empreinte GPG> <alfred-home.deb> <nouveau dossier>" >&2
    exit 2
fi

key=$1
package=$(realpath -- "$2")
version=$(dpkg-deb -f "$package" Version)
dpkg --validate-version "$version"
if [[ $(dpkg-deb -f "$package" Package) != alfred-home || $(dpkg-deb -f "$package" Architecture) != amd64 ]]; then
    echo "Le fichier doit être le paquet alfred-home amd64." >&2
    exit 2
fi
asset="alfred-home_${version}_amd64.deb"
mkdir -p -- "$(dirname -- "$3")"
output=$(realpath -m -- "$3")
if [[ -e $output || -L $output ]]; then
    echo "Le dossier de sortie existe déjà : $output" >&2
    exit 1
fi
stage=$(mktemp -d "$(dirname -- "$output")/.alfred-release.XXXXXX")
trap 'rm -rf -- "$stage"' EXIT

(
    cd -- "$stage"
    install -m 0644 -- "$package" "$asset"
    apt-ftparchive packages . > Packages
    gzip -n -c Packages > Packages.gz
    apt-ftparchive \
        -o APT::FTPArchive::Release::Origin=morrisdevstudio \
        -o APT::FTPArchive::Release::Label='Alfred Home' \
        -o APT::FTPArchive::Release::Architectures=amd64 \
        release . > .Release
    gpg --batch --local-user "$key" --output InRelease --clearsign .Release
    gpg --batch --armor --export "$key" > alfred-home.asc
    test -s alfred-home.asc
    sha256sum -- "$asset" > "$asset.sha256"
    rm -- .Release
)
chmod 0755 "$stage"
mv -T --no-clobber -- "$stage" "$output"
if [[ -d $stage ]]; then
    echo "Un autre build a créé $output." >&2
    exit 1
fi
printf 'Fichiers de release GitHub : %s\n' "$output"
