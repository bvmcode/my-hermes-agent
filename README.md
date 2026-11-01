# Hermes Agent on EC2 (Terraform)

Provisions an Ubuntu 24.04 EC2 instance and installs Nous Research's Hermes Agent on first boot.

What you get:
- t3.medium, 30 GB encrypted gp3 root volume, IMDSv2 enforced
- Security group allows the Hermes dashboard (TCP 9119) from `dashboard_allowed_cidrs` (default: anywhere). Shell access stays on SSM Session Manager
- Optional SSH (set `ssh_key_name` + `ssh_allowed_cidrs`)
- Hermes installed for the `ubuntu` user via the official installer, with the setup wizard skipped
- Dashboard starts on boot at `0.0.0.0:9119` with a username and password generated on the instance. Those credentials are not stored in Terraform

## Deploy

```bash
cp terraform.tfvars.example terraform.tfvars   # edit as needed
terraform init
terraform apply
```

The install runs in the background after boot and takes roughly 5–10 minutes.

Apply writes `infra/outputs.txt` (gitignored). That file exports `INSTANCE_ID`, and `make login` reads it from there. In a shell, `source infra/outputs.txt` sets the same variable.

## Finish setup on the instance

```bash
# connect as the ubuntu user
make login

# confirm the install finished
ls /var/lib/hermes-install-done && tail /var/log/hermes-install.log

# setup hermes model and gateway using ollama as provider
ollama serve &
hermes pm install --extra messaging
ollama launch hermes
```

Provider credentials are entered interactively so they never land in Terraform state or EC2 user data.

## Tear down

```bash
terraform destroy
```

## Hermes Desktop

Install the app on your computer from https://hermes-agent.nousresearch.com/desktop.

Hermes will not listen on the public IP until a dashboard username and password are set. The session token in `~/.hermes/.env` is not that login, and model setup does not start this port. Set `dashboard_allowed_cidrs` to your own IP if you do not want port 9119 open to the internet.

First boot writes the login and starts `hermes-dashboard`. From your computer:

```bash
make dashboard-login
```

```bash
source infra/outputs.txt
```

The remote URL is `$dashboard_url` from that file.

In the app, open Settings → Gateways → Remote gateway and enter that URL. Sign-in appears once the dashboard answers. Sign in with the username and password from the command above.

## Tailscale

One tailnet for your Mac, phone, and this agent. Create it at https://login.tailscale.com/start and sign in with the same account on each device. After all three are connected, they show up on the [Machines](https://login.tailscale.com/admin/machines) page.

### Mac

Install Tailscale from https://tailscale.com/download/macos. Open it, allow the VPN configuration, and sign in.

### Phone

Install Tailscale from the App Store or Google Play. Allow the VPN configuration and sign in with the same account.

### Agent

```bash
make login
curl -fsSL https://tailscale.com/install.sh | sh
sudo tailscale up --hostname=hermes
```

Open the login URL that command prints, on your Mac, and approve the machine. It reconnects on its own after a reboot.

```bash
tailscale ip -4
tailscale status
```

Your Mac and phone can then open the dashboard at `http://hermes:9119`. Use that URL as the remote gateway in Hermes Desktop. Tailscale reaches the instance on its own interface, so you can set `dashboard_allowed_cidrs` to `[]` and apply again to close port 9119 on the public internet.
