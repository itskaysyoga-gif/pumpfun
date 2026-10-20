# DigitalOcean setup — step by step (about 60–90 minutes, once)

You do steps 1–8 by hand. After step 8, everything else happens by talking to Claude
from claude.ai/code or the Claude phone app. Commands go in the Mac **Terminal** app
unless a step says "on the droplet".

What you'll have at the end: a server in Frankfurt running Claude Code (logged in with your
Max plan), the pumpfun repo, and the collector ready to start. Cost: $24/month droplet +
$4.80/month weekly backups = **~$29/month**, billed per second, cancel any time.

---

## 1. Make an SSH key on your Mac (skip if you already have `~/.ssh/id_ed25519.pub`)
```bash
ls ~/.ssh/id_ed25519.pub || ssh-keygen -t ed25519 -C "hussein-mac"
```
Press Enter for the default path. Set a passphrase you'll remember (recommended).
Then copy the public key to the clipboard:
```bash
pbcopy < ~/.ssh/id_ed25519.pub
```

## 2. DigitalOcean account security (2 minutes)
- Sign in at cloud.digitalocean.com → top-right avatar → **My Account** → **Security** →
  turn on **Two-factor authentication**.
- **Settings → Security → SSH Keys → Add SSH Key** → paste the key → name it `hussein-mac`.

## 3. Create the droplet
**Create → Droplets**, then choose exactly:

| Setting | Choose | Why |
| --- | --- | --- |
| Region | **Frankfurt (FRA1)** | Many Solana validators are in Frankfurt/Amsterdam; matters in Phase 7 |
| Image | **Ubuntu 24.04 (LTS) x64** | Supported by Claude Code and our scripts |
| Size | **Basic → Regular → 2 vCPU / 4 GB / 80 GB SSD ($24/mo)** | Claude Code needs 4 GB RAM. Resize later if Phase 4 needs more |
| Authentication | **SSH Key → hussein-mac** | No passwords |
| Backups | **Enable, Weekly** (+$4.80/mo) | 14+ days of collected data cannot be re-downloaded |
| Monitoring | **Tick "Add improved metrics monitoring and alerting"** (free) | CPU/disk/RAM graphs and alerts |
| Hostname | `pumplab-fra1` | |
| Tags / Project | optional | |

Click **Create Droplet**. Copy its **public IPv4** when it appears. Below, `IP` means that address.

## 4. Cloud firewall (in the DigitalOcean panel)
**Networking → Firewalls → Create Firewall**, name `pumplab-fw`:
- Inbound rules: keep only **SSH, TCP 22, All IPv4, All IPv6**. (Your home IP changes,
  so we don't lock it to one IP; keys + fail2ban protect SSH.)
- Outbound: leave the defaults (all allowed). The collector needs outbound websockets.
- **Apply to Droplets:** `pumplab-fra1` → **Create Firewall**.

## 5. Bootstrap as root (on the droplet)
```bash
ssh root@IP
```
Type `yes` at the fingerprint question. Then on the droplet:
```bash
curl -fsSL https://raw.githubusercontent.com/itskaysyoga-gif/pumpfun/main/deploy/bootstrap_root.sh -o bootstrap_root.sh
less bootstrap_root.sh        # read it (q to quit)
bash bootstrap_root.sh
```
If the repo is private, that `curl` returns 404. In that case: on your Mac run
`scp ~/path/to/pumpfun/deploy/bootstrap_root.sh root@IP:` or open the file on GitHub,
click **Raw**, and paste it into `nano bootstrap_root.sh` on the droplet.

Takes 3–5 minutes. If it asks about a config file during the upgrade, keep the local version
(the default). **Leave this root window open.**

## 6. Test the pumplab login, then lock root out
In a **new** Mac Terminal window:
```bash
ssh pumplab@IP
```
If you get a `pumplab@pumplab-fra1:~$` prompt, it works. Now, back in the **root** window:
```bash
printf 'PermitRootLogin no\nPasswordAuthentication no\nKbdInteractiveAuthentication no\n' > /etc/ssh/sshd_config.d/00-pumplab.conf
sshd -t && systemctl restart ssh
sshd -T | grep -E '^(permitrootlogin|passwordauthentication) '
```
The last line must print `permitrootlogin no` and `passwordauthentication no`. (The `00-`
file wins over DigitalOcean's own settings file because sshd uses the first value it reads.)
Check `ssh pumplab@IP` still works in another window, then type `exit` here.
From now on you only log in as `pumplab`.

## 7. Install Claude Code and the project (as pumplab, on the droplet)
```bash
curl -fsSL https://raw.githubusercontent.com/itskaysyoga-gif/pumpfun/main/deploy/bootstrap_user.sh -o bootstrap_user.sh
bash bootstrap_user.sh keys
```
(Private repo? Same as step 5: paste the file from GitHub's **Raw** view into `nano bootstrap_user.sh`.)
It prints one line starting `ssh-ed25519`. Copy it, then on GitHub:
**pumpfun repo → Settings → Deploy keys → Add deploy key** → Title `pumplab-droplet` →
paste → **tick "Allow write access"** → Add key. (This key can only touch this one repo.)

Back on the droplet:
```bash
bash bootstrap_user.sh install
exec bash -l
claude --version
```
Expect `11 passed` from the tests and a version number from `claude`.

## 8. Log Claude Code in and start Remote Control (as pumplab, on the droplet)
```bash
cd ~/pumpfun
claude
```
- Choose **Claude account (subscription)** login. It shows a URL: open it on your Mac,
  approve, paste the code back. Trust the `pumpfun` folder when asked.
- Type `/exit`.

Now start a session that keeps running after you disconnect, and that you can drive from
claude.ai/code or your phone:
```bash
tmux new -s claude
cd ~/pumpfun && claude remote-control --name pumplab
```
Answer `y` to enable Remote Control. Detach from tmux with **Ctrl+B, then D**. You can now
close the Terminal. (Re-attach later with `ssh pumplab@IP` then `tmux attach -t claude`.)

Open **claude.ai/code** (or the Code tab in the Claude app) → the **pumplab** session →
send:
```
/phase-run 1
```
Claude will run the 60-second data probe, start the collector if it passes, and report back.

---

## If something goes wrong
| Symptom | Fix |
| --- | --- |
| `Permission denied (publickey)` | Wrong key or user. `ssh -i ~/.ssh/id_ed25519 pumplab@IP` |
| Locked out completely | DigitalOcean panel → droplet → **Access → Recovery Console**, or destroy and redo (10 min) |
| `claude: command not found` | `exec bash -l`, or `~/.local/bin/claude` |
| Claude login link won't open | Copy the full URL; it must be opened in a browser logged in to your Max account |
| Remote session missing on claude.ai/code | `ssh pumplab@IP`, `tmux attach -t claude`, check it's running; restart with `claude remote-control --name pumplab` |
| Droplet rebooted | Collector restarts by itself. Re-run step 8's tmux + `claude remote-control` |

## Monthly cost summary
| Item | $/month |
| --- | --- |
| Droplet 2 vCPU / 4 GB / 80 GB | 24.00 |
| Weekly backups (20%) | 4.80 |
| Monitoring, cloud firewall | 0 |
| Claude Code | included in your Max plan |
| **Total** | **~28.80** |

Resize to 4 vCPU / 8 GB ($48) only if Phase 4 runs out of memory; Claude will tell you.
Choose **CPU and RAM only** when resizing so you can size back down.
