# Youtbe App-level OAuth credentials (for trancript service)

## How to Refresh access token
- execute script /utils/get_youtube_refresh_token.py
- authorize (in web URL) the app video2text to act on behalf of the desired user (in this case is a development user: ju.....@....com)
- copy refresh token from the console
- update YOUTUBE_OAUTH_CLIENT_REFRESH_TOKEN in file .env (for dev environment)
- update YOUTUBE_OAUTH_CLIENT_REFRESH_TOKEN in Github Environment Secrers (production)
- Note: how it actually works is that the app video2text is asking the user (in this case is a development user: ju.....@....com) to grant access to see, edit, and permanently delete your YouTube videos, ratings, comments and captions. Also by using this user ju..... the app is able to retrieve videos from the channels.


# Setup GitHub Actions Self-Hosted Runner on Google Cloud Platform VM (Compute Engine)

1. Connect to the VM
Use SSH or your cloud provider’s IAP/tunnel.

2. Update system and install basics
bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y git curl ca-certificates gnupg

3. Install Docker (Debian Bookworm, official repo)
bash
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/debian/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/debian $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
sudo systemctl enable --now docker

4. Create dedicated runner user
bash
sudo useradd -m -s /bin/bash actions-runner
sudo passwd -l actions-runner
[comment]: # only if runner needs Docker:
sudo usermod -aG docker actions-runner

5. Firewall (UFW) — don’t lock yourself out
bash
sudo apt install -y ufw
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow out 80/tcp
sudo ufw allow out 443/tcp
[comment]: # if you use direct SSH, allow your IP before enabling:
[comment]: # sudo ufw allow from YOUR_IP/CIDR to any port 22 proto tcp
sudo ufw enable

6. Download and register GitHub Actions Runner (!!!! ---> BETTER follow GitHub Actions website instructions)
Generate a registration token on GitHub: Repo/Org → Settings → Actions → Runners → New self-hosted runner.
As the actions-runner user on the VM, download, extract and configure the runner:
bash
[comment]: # run as actions-runner (or sudo -u actions-runner -i)
[comment]: # fetch latest release tag, download tarball, extract (example pattern)
RUNNER_VERSION=$(curl -s https://api.github.com/repos/actions/runner/releases/latest | grep -Po '"tag_name": "\K.*?(?=")')
ARCH=$(uname -m); [ "$ARCH" = "x86_64" ] && ARCH="x64" || true
TAR="actions-runner-${RUNNER_VERSION:1}-linux-${ARCH}.tar.gz"
curl -fsSLo $TAR "https://github.com/actions/runner/releases/download/${RUNNER_VERSION}/${TAR}"
tar xzf $TAR && rm -f $TAR
[comment]: # run the config step (replace URL and TOKEN)
./config.sh --url https://github.com/OWNER/REPO --token YOUR_TOKEN --work _work --labels self-hosted,linux,ci-debian-bookworm-01 --unattended

7. Install runner as a service and start
Use the runner-provided helper or systemd unit:
bash
[comment]: # runner helper (from runner directory)
sudo ./svc.sh install
sudo ./svc.sh start

[comment]: # or a minimal systemd unit (example)
[comment]: # /etc/systemd/system/github-actions-runner.service
[comment]: # [Unit]...
[comment]: # [Service] ExecStart=/home/actions-runner/actions-runner/run.sh User=actions-runner
[comment]: # Then:
sudo systemctl daemon-reload
sudo systemctl enable --now github-actions-runner.service

8. Verify and test
bash
[comment]: # check runner service logs
sudo journalctl -u github-actions-runner -f

[comment]: # quick Docker smoke test
docker run --rm hello-world
Confirm the runner appears as "online" in GitHub (Repo/Org → Settings → Actions → Runners).

9. Update workflow to target the runner
Set runs-on to include your label in your workflow YAML:

yaml
runs-on: [self-hosted, linux, ci-debian-bookworm-01]
Add required GitHub Secrets/Vars in repo Settings.

10. Operational notes (one-liners)
Disable automatic workflow runs from forks or require approval in GitHub Actions settings.

Use /home/actions-runner/_work or a mounted disk for runner workdir.

Snapshot VM before big changes; rotate secrets and prune images periodically (docker system prune -af).

11. Run github actions self-hosted runner job in VM
bash
./run.sh