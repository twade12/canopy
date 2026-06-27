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

## 2. systemd service

```bash
sudo cp deploy/canopy.service /etc/systemd/system/canopy.service
sudoedit /etc/systemd/system/canopy.service     # set CANOPY_PASSWORD and model
sudo systemctl daemon-reload
sudo systemctl enable --now canopy
systemctl status canopy
curl -s localhost:8088/healthz                  # -> {"ok":true}
```

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

## Notes & hardening

- **CAN bench over the web:** the `/api/can/*` endpoints talk to a CAN interface on the
  *server*. For a hosted instance that means a USB-to-CAN adapter on the host, or `vcan0`.
  Remote/per-technician benches will use the agent model in [GAMEPLAN.md](GAMEPLAN.md).
- **Backups:** back up `/var/lib/canopy/vision` (SQLite DB + `uploads/` + `secret.key`).
- **Single password today; real accounts later.** Multi-user auth, per-tech identity, and
  roles are in [GAMEPLAN.md](GAMEPLAN.md) §Auth.
- **Firewall:** only expose 80/443. Keep `8088` bound to localhost (the unit already does).
