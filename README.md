# Hermes Agent on EC2

Ubuntu 24.04 instance that runs [Hermes Agent](https://hermes-agent.nousresearch.com/) with [Ollama](https://ollama.com/) as its model server. Models stay on the box: Ollama listens on `127.0.0.1:11434`, and Hermes uses that endpoint. No cloud LLM API key.

First boot installs both, writes a dashboard username and password, and starts the dashboard on `0.0.0.0:9119`. Those credentials are not in Terraform state or user data. Shell access is SSM Session Manager. SSH is off unless you set `ssh_key_name` and `ssh_allowed_cidrs`. The root volume is encrypted gp3, and the instance requires IMDSv2.

`t3.medium` (4 GB RAM, 30 GB disk) is only enough to boot. Hermes needs a tool-calling model and about a 64k context; a model that can do that wants roughly 24 GB of RAM and extra disk for the weights. Set `instance_type` and `root_volume_size_gb` in `infra/terraform.tfvars` before apply. This stack is CPU-only, so replies are slow.

## Deploy

From `infra/`:

```bash
cp terraform.tfvars.example terraform.tfvars   # edit as needed
terraform init
terraform apply
```

The install keeps running after apply, for about 5–10 minutes. Apply writes `infra/outputs.txt` (gitignored). `make login` reads `INSTANCE_ID` from it. From the repo root, `source infra/outputs.txt` exports the same values, including `dashboard_url`.

## Point Hermes at Ollama

```bash
make login
ls /var/lib/hermes-install-done && tail /var/log/hermes-install.log
ollama launch hermes
```

Ollama is already a systemd service, so it does not need `ollama serve`. `ollama launch hermes` picks a model, sets the provider to `http://127.0.0.1:11434/v1`, and can connect Telegram, Discord, Slack, WhatsApp, Signal, or email. Platform tokens are entered in that session. Change the model later with `hermes model`, or connect chat later with `hermes gateway setup`.

Ollama's default context is 2048 tokens. If tool calls fail, raise it to at least 64000. See [Ollama's Hermes guide](https://docs.ollama.com/integrations/hermes) and [Hermes's local Ollama guide](https://hermes-agent.nousresearch.com/docs/guides/local-ollama-setup).

## Desktop

Install the app from https://hermes-agent.nousresearch.com/desktop. From the repo root:

```bash
make dashboard-login
source infra/outputs.txt
```

`make dashboard-login` prints the username and password from the instance. In the app, open Settings → Gateways → Remote gateway and enter `$dashboard_url`.

Port 9119 follows `dashboard_allowed_cidrs` (default: anywhere). Narrow that to your IP, or set it to `[]` once you use Tailscale.

## Tailscale

One tailnet for your Mac, phone, and this instance. Create it at https://login.tailscale.com/start and use the same account on each device.

On your Mac, install Tailscale from https://tailscale.com/download/macos. On your phone, install it from the App Store or Google Play.

On the instance:

```bash
make login
curl -fsSL https://tailscale.com/install.sh | sh
sudo tailscale up --hostname=hermes
```

Open the login URL on your Mac and approve the machine. It reconnects after a reboot. `tailscale ip -4` prints its address. The dashboard is then `http://hermes:9119`. Use that URL as the remote gateway, then set `dashboard_allowed_cidrs = []` and apply again to close port 9119 on the public internet.

## Tear down

```bash
cd infra && terraform destroy
```
