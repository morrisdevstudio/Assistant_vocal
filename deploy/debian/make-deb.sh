#!/usr/bin/env bash
set -euo pipefail

if [[ $# != 3 || ! $2 =~ ^[1-9][0-9]*$ ]]; then
    echo "Usage : bash make-deb.sh <archive Alfred extraite> <révision Debian> <sortie>" >&2
    exit 2
fi

bundle=$(cd -- "$1" && pwd)
release=$(<"$bundle/RELEASE")
if [[ ! $release =~ ^[0-9]+\.[0-9]+\.[0-9]+[A-Za-z0-9.+-]*-[0-9a-f]{12}$ ]]; then
    echo "Identifiant de version Alfred invalide." >&2
    exit 2
fi
version="${release%-*}-$2"
dpkg --validate-version "$version"
mkdir -p -- "$3"
output=$(cd -- "$3" && pwd)
file="alfred-home_${version}_amd64.deb"
if [[ -e $output/$file ]]; then
    echo "Le paquet $file existe déjà. Réutilisez-le ou choisissez une autre révision Debian." >&2
    exit 1
fi

work=$(mktemp -d)
trap 'rm -rf -- "$work"' EXIT
package="$work/package"
mkdir -p -- "$package/DEBIAN" "$package/usr/lib/alfred-home/bundle" "$package/usr/share/doc/alfred-home" "$package/usr/lib/systemd/system"
for directory in alfred bin pwa wheels; do
    cp -a -- "$bundle/$directory" "$package/usr/lib/alfred-home/bundle/"
done
for filename in RELEASE install.py health.py updater.py alfred.service constraints.txt runtime.txt README.md; do
    cp -- "$bundle/$filename" "$package/usr/lib/alfred-home/bundle/"
done
cp -- "$bundle/README.md" "$package/usr/share/doc/alfred-home/README.md"
install -m 0644 -- "$bundle/"{alfred-home-update.path,alfred-home-update.service,alfred-home-auto-update.timer,alfred-home-auto-update.service} "$package/usr/lib/systemd/system/"
size=$(du -sk "$package" | cut -f1)

cat > "$package/DEBIAN/control" <<EOF
Package: alfred-home
Version: $version
Section: sound
Priority: optional
Architecture: amd64
Maintainer: morrisdevstudio
Homepage: https://github.com/morrisdevstudio/Assistant_vocal
Depends: python3 (>= 3.13), python3 (<< 3.14), python3-venv, libc6 (>= 2.41), libgcc-s1, libstdc++6, libgomp1, libsndfile1, ca-certificates, systemd, passwd, util-linux
Installed-Size: $size
Description: Assistant vocal Alfred pour la maison
 API locale, transcription Parakeet et synthèse Phonon avec service systemd.
EOF

cat > "$package/DEBIAN/postinst" <<'EOF'
#!/bin/sh
set -e
if [ "$1" = configure ]; then
    python3 /usr/lib/alfred-home/bundle/install.py --apt
    python3 -EsB /usr/lib/alfred-home/bundle/updater.py record
    systemctl enable --now alfred-home-update.path alfred-home-auto-update.timer
fi
EOF

cat > "$package/DEBIAN/prerm" <<'EOF'
#!/bin/sh
set -e
if [ "$1" = remove ]; then
    systemctl disable --now alfred-home-update.path alfred-home-auto-update.timer
    if [ -f /etc/systemd/system/alfred-home.service ]; then
        systemctl stop alfred-home.service
        systemctl disable alfred-home.service
    fi
fi
EOF

cat > "$package/DEBIAN/postrm" <<'EOF'
#!/bin/sh
set -e
case "$1" in
    remove|purge)
        rm -f /etc/systemd/system/alfred-home.service
        if [ -d /run/systemd/system ]; then systemctl daemon-reload; fi
        ;;
esac
EOF

chmod 0755 "$package/DEBIAN/"{postinst,prerm,postrm}
dpkg-deb --root-owner-group -Zzstd --build "$package" "$work/$file"
mv --no-clobber -- "$work/$file" "$output/$file"
if [[ -e $work/$file ]]; then
    echo "Un autre build a créé $output/$file." >&2
    exit 1
fi
(cd "$output" && sha256sum -- "$file" > "$file.sha256")
printf 'Paquet APT : %s/%s\n' "$output" "$file"
