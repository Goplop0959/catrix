#!/usr/bin/env bash
# Catrix installer — the ONLY supported install method:
#   curl -fsSL https://raw.githubusercontent.com/Goplop0959/Catrix/refs/heads/master/Installer.sh | sudo bash
#
# Adds this GitHub repo as a signed apt source, then installs the `catrix`
# Debian package with apt. Needs root (hence sudo): writing to
# /etc/apt/sources.list.d and /usr/share/keyrings requires it.
set -euo pipefail

REPO="Goplop0959/Catrix"
BRANCH="master"
RAW="https://raw.githubusercontent.com/${REPO}/refs/heads/${BRANCH}"
KEYRING="/usr/share/keyrings/catrix-archive-keyring.gpg"
SOURCE="/etc/apt/sources.list.d/catrix.sources"

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

echo "catrix: fetching archive key..."
curl -fsSL "${RAW}/catrix-archive-keyring.gpg" -o "${TMP}/keyring.gpg"
install -D -m 0644 "${TMP}/keyring.gpg" "$KEYRING"

echo "catrix: adding apt source..."
cat > "$SOURCE" <<EOF
Types: deb
URIs: https://raw.githubusercontent.com/${REPO}/refs/heads/${BRANCH}
Suites: stable
Components: main
Architectures: amd64 arm64 armhf i386
Signed-By: ${KEYRING}
EOF

echo "catrix: updating apt metadata..."
apt-get update -o Dir::Etc::sourcelist="sources.list.d/catrix.sources" \
    -o Dir::Etc::sourceparts="-" -o APT::Get::List-Cleanup="0"

echo "catrix: installing package..."
apt-get install -y catrix
echo "catrix: done. Run: catrix"
