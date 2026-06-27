# Deploying CANOPY Vision on the web

Host the wiring-diagram + diagnostics app on your own domain: a `systemd` service runs the
app on `127.0.0.1:8088`, and nginx terminates TLS on `443` and proxies in. A single shared
password (`CANOPY_PASSWORD`) gates access; everything else (Ollama model, data) stays on
your box.

> **Prerequisite:** a host with **Ollama** running locally and the models pulled
> (`ollama pull gemma4:26b nomic-embed-text`). The app and Ollama can be on the same VM, or
> point `CANOPY_OLLAMA_URL` at another reachable host.

## 1. Install the app

```bash
sudo useradd -r -m -d /opt/canopy canopy        # service user
sudo mkdir -p /opt/canopy /var/lib/canopy/vision
sudo chown -R canopy:canopy /opt/canopy /var/lib/canopy

sudo -u canopy git clone <your-canopy-remote> /opt/canopy
cd /opt/canopy
sudo -u canopy python3 -m venv .venv
sudo -u canopy .venv/bin/pip install -e ".[vision]"
```

## 2. systemd services (app + database)

Two units: `canopy-db` (an isolated Postgres+pgvector container) and `canopy` (the app on
127.0.0.1:8088, which `Wants`/`After` the DB). The DB unit publishes **port 5440** (5432 is
often already taken) — keep it in sync with `CANOPY_DATABASE_URL` in `canopy.service`.

```bash
sudo cp deploy/canopy-db.service deploy/canopy.service /etc/systemd/system/
sudoedit /etc/systemd/system/canopy.service     # set CANOPY_PASSWORD, model, paths, keys
sudo systemctl daemon-reload
sudo systemctl enable --now canopy-db canopy    # DB starts first, then the app
systemctl status canopy
curl -s localhost:8088/healthz                  # -> {"ok":true}
```

> Prefer SQLite (single box, no DB)? Just omit `canopy-db` and unset `CANOPY_DATABASE_URL`
> in `canopy.service`. Switching to Postgres starts a **fresh** knowledge base (existing
> SQLite projects stay in the SQLite file).

Set **`CANOPY_PASSWORD`** to a strong value — it's the only thing protecting a public
deployment. The signing secret is generated automatically at
`/var/lib/canopy/vision/secret.key` (keep it; deleting it logs everyone out).

## 3. nginx + TLS

```bash
# point an A/AAAA record for canopy.example.com at this host first, then:
sudo cp deploy/nginx-canopy.conf /etc/nginx/sites-available/canopy
sudo sed -i 's/canopy.example.com/YOUR.DOMAIN/g' /etc/nginx/sites-available/canopy
sudo ln -s /etc/nginx/sites-available/canopy /etc/nginx/sites-enabled/
sudo certbot --nginx -d YOUR.DOMAIN            # issues + wires the cert
sudo nginx -t && sudo systemctl reload nginx
```

Browse to `https://YOUR.DOMAIN` → you'll get the login page.

The nginx config disables proxy buffering on `…/stream` endpoints so the **streaming chat
and Assistant** work through the proxy, and raises timeouts for slow large-model calls.

## 4. Updating

```bash
cd /opt/canopy && sudo -u canopy git pull
sudo -u canopy .venv/bin/pip install -e ".[vision]"
sudo systemctl restart canopy
```

## Access from your phone + laptop on the LAN / VPN

To reach CANOPY from other devices on the same network (so you can pair a phone and snap
board photos), bind the app to all interfaces instead of localhost. In the installed
`canopy.service`, change the host in `ExecStart`:

```ini
ExecStart=/home/<you>/Documents/canopy/.venv/bin/uvicorn --factory canopy.vision.app:create_app \
          --host 0.0.0.0 --port 8088 --timeout-keep-alive 75
```

```bash
sudo systemctl daemon-reload && sudo systemctl restart canopy
hostname -I            # find this machine's LAN/VPN IP, e.g. 192.168.1.50
```

Then browse to `http://192.168.1.50:8088` from any device on the network (or VPN) and log
in with `CANOPY_PASSWORD`. The **Pair phone** button (in the Triage and PCB tabs) shows a QR
that opens a phone capture page bound to that project — photos you take appear on your laptop
in real time. The pairing link is built from the address you used, so it must be the LAN/VPN
IP (not `127.0.0.1`).

> Binding `0.0.0.0` exposes the app to your LAN — the password is the only gate, so use a
> strong one. For internet exposure use the nginx + TLS setup above instead (keep the app on
> `127.0.0.1`).

## Migrate existing SQLite data into Postgres

Switching to Postgres starts empty. To carry your existing local projects over:

```bash
# with CANOPY_DATABASE_URL set (or pass --to):
.venv/bin/canopy vision migrate
# or explicitly:
.venv/bin/canopy vision migrate --sqlite ~/.canopy/vision/canopy_vision.db \
    --to postgresql://canopy:canopy@127.0.0.1:5440/canopy
```

It copies every project, diagram, pinout, tag, memory (with embeddings), chat/triage
transcript, and attachment. Run it once into a fresh DB.

## Shared knowledge base (Postgres + pgvector)

By default the app uses a local SQLite file (fine for a single box). For a team — shared
knowledge across technicians and org-wide semantic search — point it at **Postgres with
pgvector**:

```bash
# quickest: the official pgvector image
docker run -d --name canopy-db -e POSTGRES_PASSWORD=canopy -e POSTGRES_USER=canopy \
    -e POSTGRES_DB=canopy -p 5432:5432 pgvector/pgvector:pg16
# (or `docker compose up -d db` for the Timescale+pgvector image in this repo)
```

Then set on the service:

```ini
Environment=CANOPY_DATABASE_URL=postgresql://canopy:canopy@localhost:5432/canopy
```

The schema (incl. the `vector` extension) is created automatically on first boot. Uploaded
files still live under `CANOPY_VISION_DATA/uploads` — back both up. (Object storage for
files and full server-side ANN search are in [GAMEPLAN.md](GAMEPLAN.md).)

## Notes & hardening

- **CAN bench over the web:** the `/api/can/*` endpoints talk to a CAN interface on the
  *server*. For a hosted instance that means a USB-to-CAN adapter on the host, or `vcan0`.
  Remote/per-technician benches will use the agent model in [GAMEPLAN.md](GAMEPLAN.md).
- **Backups:** back up `/var/lib/canopy/vision` (SQLite DB + `uploads/` + `secret.key`).
- **Single password today; real accounts later.** Multi-user auth, per-tech identity, and
  roles are in [GAMEPLAN.md](GAMEPLAN.md) §Auth.
- **Firewall:** only expose 80/443. Keep `8088` bound to localhost (the unit already does).
