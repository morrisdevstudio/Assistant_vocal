#!/usr/bin/env bash
set -euo pipefail
umask 022

if [[ $# != 4 || ! $2 =~ ^(dev|prod)$ || ! $3 =~ ^([[:xdigit:]]{40}|[[:xdigit:]]{64})$ ]]; then
    echo "Usage : bash apt-repo.sh <racine du dépôt> <dev|prod> <empreinte GPG> <alfred-home.deb>" >&2
    exit 2
fi

package=$(realpath -- "$4")
version=$(dpkg-deb -f "$package" Version)
dpkg --validate-version "$version"
if [[ $(dpkg-deb -f "$package" Package) != alfred-home || $(dpkg-deb -f "$package" Architecture) != amd64 ]]; then
    echo "Le fichier doit être le paquet alfred-home amd64." >&2
    exit 2
fi
file="alfred-home_${version}_amd64.deb"
channel="$1/$2"
key=$3
mkdir -p -- "$channel/pool" "$channel/by-hash/SHA256"
channel=$(cd -- "$channel" && pwd)
exec 9> "$channel/.publish.lock"
flock 9

stage=$(mktemp -d "$channel/.publish.XXXXXX")
trap 'rm -rf -- "$stage"' EXIT
mkdir -- "$stage/pool"
shopt -s nullglob
for existing in "$channel"/pool/*.deb; do
    ln -- "$existing" "$stage/pool/"
done
if [[ -e $stage/pool/$file ]]; then
    if ! cmp -s -- "$package" "$stage/pool/$file"; then
        echo "La version $version est déjà publiée avec un contenu différent." >&2
        exit 1
    fi
else
    install -m 0644 -- "$package" "$stage/pool/$file"
fi

(
    cd -- "$stage"
    apt-ftparchive packages pool > Packages
    gzip -n -c Packages > Packages.gz
    apt-ftparchive \
        -o APT::FTPArchive::Release::Origin=morrisdevstudio \
        -o APT::FTPArchive::Release::Label="Alfred Home $2" \
        -o APT::FTPArchive::Release::Architectures=amd64 \
        -o APT::FTPArchive::Release::Acquire-By-Hash=yes \
        release . > Release
    gpg --batch --local-user "$key" --output InRelease --clearsign Release
    gpg --batch --armor --export "$key" > alfred-home.asc
    test -s alfred-home.asc
)

if [[ ! -e $channel/pool/$file ]]; then
    mv -- "$stage/pool/$file" "$channel/pool/$file"
fi
for index in Packages Packages.gz; do
    hash=$(sha256sum -- "$stage/$index" | cut -d ' ' -f1)
    if [[ ! -e $channel/by-hash/SHA256/$hash ]]; then
        ln -- "$stage/$index" "$stage/hash"
        mv -- "$stage/hash" "$channel/by-hash/SHA256/$hash"
    fi
done
# L'index signé devient visible après tous les fichiers qu'il référence.
for name in Packages Packages.gz Release alfred-home.asc InRelease; do
    mv -- "$stage/$name" "$channel/$name"
done
printf 'Dépôt APT %s : %s\n' "$2" "$channel"
