# catrix 🐈‍⬛

Matrix-style falling cat faces for your terminal. Like `cmatrix`, but cats —
random cat faces rain down your screen in columns, default color **green**,
bright head fading into the dark. Wake up, Neo… the cats have you.

A Debian package (`all` arch, pure shell — no Python needed). Inspired by
[cmatrix](https://github.com/abishekvashok/cmatrix) and
*The Matrix Resurrections* (2021). Open source (MIT).

## Install (only method)

```bash
curl -fsSL https://raw.githubusercontent.com/Goplop0959/Catrix/refs/heads/master/Installer.sh | sudo bash
```

It needs `sudo` because it registers this GitHub repo as a **signed apt
source** (`/etc/apt/sources.list.d/catrix.sources` + keyring in
`/usr/share/keyrings/`) and then installs the `catrix` package with `apt`.
The Release metadata is GPG-signed; apt verifies it on every update.

## Usage

```bash
catrix                  # green rain (default)
catrix -C magenta       # green red blue white yellow magenta cyan
catrix -b / --no-bold   # bold head faces on/off (default on)
catrix -u 50            # frame delay in ms (default 80, lower = faster)
catrix -d 90            # rain density percent 0-100 (default 70)
catrix update           # refresh apt metadata (cache-bypassed) + upgrade
catrix --help
```

### Keys

| Key         | Action                    |
|-------------|---------------------------|
| `q` / `Esc` | quit                      |
| `space`     | pause / resume            |
| `+` / `-`   | faster / slower           |
| `c`         | cycle rain color          |
| `b`         | toggle bold heads         |

## Update

`catrix update` runs `apt-get update` with cache-bypass directives (so no
stale `Packages`/`Release` can be served — the request is changed in a
useless-but-effective way) and then upgrades only `catrix`:

```bash
sudo apt-get update -o Acquire::https::No-Cache=true -o Acquire::http::No-Cache=true
sudo apt-get install -y --only-upgrade catrix
```

## Trust / verification

Releases are signed with the maintainer key below (repo metadata in
`dists/`, package checksums in `Release`, detached + clearsigned via
`InRelease`/`Release.gpg`). apt checks all of this automatically because the
source entry pins `Signed-By` to our keyring.

- Key: `Catrix Release Signing <catrix@goplop0959>`, RSA 4096
- Fingerprint: `29ACAB43B1F23F95F77B38DB5BE51EFAD981083A`
- Public key: [`catrix-archive-keyring.gpg`](catrix-archive-keyring.gpg)
  (binary keyring, also as
  [`catrix-archive-keyring.asc`](catrix-archive-keyring.asc))

Maintainer rebuild + re-sign after a change (needs the **private** key,
which is never committed — back it up somewhere safe):

```bash
python3 packaging/build_repo.py --version 1.0.1 --key 29ACAB43B1F23F95F77B38DB5BE51EFAD981083A
git add -A && git commit -m "catrix 1.0.1" && git push
```

## Faces

The rain set is in [`faces.txt`](faces.txt) (entries separated by
`\n:|:\n`) and embedded in the `catrix` script. Sources: the
[cat-ascii-faces](https://github.com/melaniecebula/cat-ascii-faces) collection
(MIT) plus community combos from [emojicombos.com](https://emojicombos.com)
(including the cat with a gun `(=ↀωↀ=)▄︻┻┳═一`).

## Credits

- *The Matrix Resurrections* (2021) — red pill, blue pill, cat pill.
- `cmatrix` — the original falling-text screensaver.
- [melaniecebula/cat-ascii-faces](https://github.com/melaniecebula/cat-ascii-faces) — face collection (MIT).
- emojicombos.com contributors — combo faces.

## License

MIT — see [LICENSE](LICENSE).
