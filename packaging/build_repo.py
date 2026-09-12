#!/usr/bin/env python3
"""Build the catrix .deb and the GitHub-hosted apt repo metadata.

Stdlib only (+ gpg CLI for signing). Run from the repo root:

    python3 packaging/build_repo.py --version 1.0.0 \\
        --key 29ACAB43B1F23F95F77B38DB5BE51EFAD981083A

Produces:
  pool/main/c/catrix/catrix_<ver>_all.deb
  dists/stable/main/binary-{amd64,arm64,armhf,i386}/{Packages,Packages.gz}
  dists/stable/{Release,InRelease,Release.gpg}
  catrix-archive-keyring.{gpg,asc}

The private signing key is NEVER written here; it stays in your keyring.
"""
import argparse
import gzip
import hashlib
import io
import os
import struct
import subprocess
import sys
import tarfile
import time

ARCHES = ["amd64", "arm64", "armhf", "i386"]
MAINTAINER = "Powerentity <43914558+Goplop0959@users.noreply.github.com>"
HOMEPAGE = "https://github.com/Goplop0959/Catrix"
MTIME = 1720000000


def ar_entry(name, data):
    name = name.encode()[:16].ljust(16, b" ")
    head = name + b"%-12d%-6d%-6d%-8o%-10d`\n" % (MTIME, 0, 0, 0o100644, len(data))
    if len(data) % 2:
        data += b"\n"
    return head + data


def make_ar(members):
    out = b"!<arch>\n"
    for name, data in members:
        out += ar_entry(name, data)
    return out


def tar_bytes(files, compress):
    """files: list of (arcname, bytes, mode). Returns (gz|xz) bytes."""
    buf = io.BytesIO()
    mode = "w:gz" if compress == "gz" else "w:xz"
    with tarfile.open(fileobj=buf, mode=mode, pax_headers={}) as tf:
        for arcname, data, fmode in files:
            ti = tarfile.TarInfo(arcname)
            ti.size = len(data)
            ti.mtime = MTIME
            ti.uid = ti.gid = 0
            ti.uname = ti.gname = "root"
            ti.mode = fmode
            tf.addfile(ti, io.BytesIO(data))
    return buf.getvalue()


def build_deb(root, version):
    with open(os.path.join(root, "catrix"), "rb") as fh:
        script = fh.read()
    with open(os.path.join(root, "LICENSE"), "rb") as fh:
        license_text = fh.read()
    with open(os.path.join(root, "README.md"), "rb") as fh:
        readme = fh.read()
    changelog = (
        "catrix (%s) stable; urgency=medium\n\n"
        "  * Release %s.\n\n"
        " -- %s  %s\n" % (version, version, MAINTAINER,
                          time.strftime("%a, %d %b %Y %H:%M:%S +0000", time.gmtime(MTIME)))
    ).encode()
    control = (
        "Package: catrix\n"
        "Version: %s\n"
        "Section: games\n"
        "Priority: optional\n"
        "Architecture: all\n"
        "Maintainer: %s\n"
        "Depends: bash\n"
        "Recommends: sudo\n"
        "Homepage: %s\n"
        "Description: Matrix-style falling cat faces for your terminal\n"
        " Like cmatrix, but cats. Random cat faces rain down the screen\n"
        " in columns, default green. Includes the `catrix update` command.\n" % (version, MAINTAINER, HOMEPAGE)
    ).encode()
    copyright_text = (
        "Format: https://www.debian.org/doc/packaging-manuals/copyright-format/1.0/\n"
        "Source: https://github.com/Goplop0959/Catrix\n\n"
        "Files: *\nCopyright: 2026 Powerentity\nLicense: MIT\n"
    ).encode() + license_text

    data_files = [
        ("./usr/bin/catrix", script, 0o755),
        ("./usr/share/doc/catrix/copyright", copyright_text, 0o644),
        ("./usr/share/doc/catrix/README.md", readme, 0o644),
        ("./usr/share/doc/catrix/changelog.Debian.gz", gzip.compress(changelog, mtime=MTIME), 0o644),
    ]
    data_blob = tar_bytes(data_files, "xz")
    md5sums = "".join(
        "%s  %s\n" % (hashlib.md5(d).hexdigest(), n.lstrip("./"))
        for n, d, _ in data_files
    ).encode()
    control_files = [
        ("./control", control, 0o644),
        ("./md5sums", md5sums, 0o644),
    ]
    deb = make_ar([
        ("debian-binary", b"2.0\n"),
        ("control.tar.gz", tar_bytes(control_files, "gz")),
        ("data.tar.xz", data_blob),
    ])
    pool_dir = os.path.join(root, "pool", "main", "c", "catrix")
    os.makedirs(pool_dir, exist_ok=True)
    deb_name = "catrix_%s_all.deb" % version
    with open(os.path.join(pool_dir, deb_name), "wb") as fh:
        fh.write(deb)
    return "pool/main/c/catrix/" + deb_name, deb


def hashes(path):
    with open(path, "rb") as fh:
        data = fh.read()
    return {
        "size": len(data),
        "md5": hashlib.md5(data).hexdigest(),
        "sha1": hashlib.sha1(data).hexdigest(),
        "sha256": hashlib.sha256(data).hexdigest(),
    }


def gpg_path(path):
    """msys gpg (Git for Windows) mangles backslash paths: give it POSIX form."""
    if os.name == "nt":
        path = os.path.abspath(path)
        drive, rest = os.path.splitdrive(path)
        if drive:
            path = "/%s%s" % (drive[0].lower(), rest.replace("\\", "/"))
        else:
            path = path.replace("\\", "/")
    return path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--version", required=True)
    ap.add_argument("--key", required=True, help="GPG key id/fingerprint for signing")
    ap.add_argument("--root", default=".")
    args = ap.parse_args()
    root = os.path.abspath(args.root)

    deb_rel, _deb = build_deb(root, args.version)
    print("built %s" % deb_rel)

    entry = (
        "Package: catrix\n"
        "Version: %s\n"
        "Architecture: all\n"
        "Maintainer: %s\n"
        "Depends: bash\n"
        "Recommends: sudo\n"
        "Homepage: %s\n"
        "Filename: %s\n" % (args.version, MAINTAINER, HOMEPAGE, deb_rel)
    )
    h = hashes(os.path.join(root, deb_rel))
    entry += ("Size: %d\nMD5sum: %s\nSHA1: %s\nSHA256: %s\n"
              "Description: Matrix-style falling cat faces for your terminal\n" % (
                  h["size"], h["md5"], h["sha1"], h["sha256"]))

    dists = os.path.join(root, "dists", "stable", "main")
    rel_entries = []
    for arch in ARCHES:
        d = os.path.join(dists, "binary-" + arch)
        os.makedirs(d, exist_ok=True)
        for name, data in (("Packages", entry.encode()),
                           ("Packages.gz", gzip.compress(entry.encode(), mtime=MTIME))):
            with open(os.path.join(d, name), "wb") as fh:
                fh.write(data)
            rel = "main/binary-%s/%s" % (arch, name)
            hh = hashes(os.path.join(d, name))
            rel_entries.append((rel, hh))

    date = time.strftime("%a, %d %b %Y %H:%M:%S UTC", time.gmtime())
    release = (
        "Origin: Catrix\nLabel: Catrix\nSuite: stable\nCodename: stable\n"
        "Date: %s\nArchitectures: %s\nComponents: main\n"
        "Description: Catrix apt repository\n" % (date, " ".join(ARCHES))
    )
    for algo, field in (("md5", "MD5Sum"), ("sha1", "SHA1"), ("sha256", "SHA256")):
        release += field + ":\n"
        for rel, hh in rel_entries:
            release += " %s %8d %s\n" % (hh[algo], hh["size"], rel)
    dist_dir = os.path.join(root, "dists", "stable")
    with open(os.path.join(dist_dir, "Release"), "w", newline="\n") as fh:
        fh.write(release)

    env = dict(os.environ)
    env["GNUPGHOME"] = env.get("GNUPGHOME", os.path.expanduser("~/.gnupg"))
    dist_posix = gpg_path(dist_dir)
    root_posix = gpg_path(root)
    subprocess.run(["gpg", "--batch", "--yes", "--pinentry-mode", "loopback",
                    "--local-user", args.key, "--clearsign",
                    "-o", dist_posix + "/InRelease",
                    dist_posix + "/Release"], check=True, env=env)
    subprocess.run(["gpg", "--batch", "--yes", "--pinentry-mode", "loopback",
                    "--local-user", args.key, "--armor", "--detach-sign",
                    "-o", dist_posix + "/Release.gpg",
                    dist_posix + "/Release"], check=True, env=env)
    # NOTE: file -o writes are unreliable under msys gpg; pipe via stdio.
    exp = subprocess.run(["gpg", "--batch", "--yes", "--armor",
                          "--export", args.key],
                         check=True, capture_output=True, env=env)
    with open(os.path.join(root, "catrix-archive-keyring.asc"), "wb") as fh:
        fh.write(exp.stdout)
    dearm = subprocess.run(["gpg", "--batch", "--yes", "--dearmor"],
                           input=exp.stdout, capture_output=True, env=env)
    if len(dearm.stdout) < 100 or dearm.stdout[0] not in (0x99, 0xC6):
        raise RuntimeError("dearmor produced unexpected output")
    with open(os.path.join(root, "catrix-archive-keyring.gpg"), "wb") as fh:
        fh.write(dearm.stdout)
    print("exported keyring (asc+gpg)")
    print("signed Release (InRelease + Release.gpg), exported keyring")


if __name__ == "__main__":
    main()
