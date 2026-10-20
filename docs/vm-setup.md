# VM setup (owner does this once, ~30 minutes)

Why a VM: the collector must run 24/7, and nothing in this project should run on a
laptop that holds personal wallets or work logins. Vercel is not suitable: its
functions can't hold a 24/7 websocket.

## 1. Create the server
- Provider: Hetzner Cloud (cheapest) or DigitalOcean. Region: Germany or Netherlands.
- Size: 2 vCPU, 4 GB RAM, 40 GB disk, Ubuntu 24.04. About $5–10/month.
- Login: add your SSH public key during creation. No password login.

## 2. Harden and install (paste as root)
```bash
apt update && apt -y upgrade && apt -y install git unattended-upgrades ufw
ufw allow OpenSSH && ufw --force enable
adduser --disabled-password --gecos "" pumplab
su - pumplab -c 'curl -LsSf https://astral.sh/uv/install.sh | sh'
```

## 3. Get the code (as pumplab)
```bash
su - pumplab
git clone https://github.com/itskaysyoga-gif/pumpfun.git
cd pumpfun && cp .env.example .env
~/.local/bin/uv sync && ~/.local/bin/uv run pytest -q
```
The repo is private? Create a read-only deploy key in GitHub (repo → Settings →
Deploy keys) and clone with the SSH URL instead.

## 4. Run the 60-second probe (the go/stop check for the data path)
```bash
~/.local/bin/uv run python scripts/probe_logs.py 60
```
Paste the full output back to Claude. Three outcomes:
- **OK** → continue to step 5.
- **Subscribe rejected / disconnects** → sign up for a free Helius key, put its
  `wss://` URL in `.env` as `RPC_WS_URL`, run the probe again.
- **"most tx had no Program data events"** → stop; Claude changes the collector.

## 5. Start the collector permanently (as root)
```bash
cp /home/pumplab/pumpfun/deploy/pumplab-collector.service /etc/systemd/system/
systemctl daemon-reload && systemctl enable --now pumplab-collector
journalctl -u pumplab-collector -f   # watch it; Ctrl+C to exit
```

## 6. Optional: Telegram alerts
Message @BotFather → /newbot → copy the token. Message your bot once, then open
`https://api.telegram.org/bot<TOKEN>/getUpdates` to find your chat id. Put both in
`.env` and `systemctl restart pumplab-collector`.

## 7. Hourly Parquet rollup (as pumplab)
```bash
crontab -e
# add:
5 * * * * cd ~/pumpfun && ~/.local/bin/uv run python -m pumplab.store.rollup >> ~/rollup.log 2>&1
```
