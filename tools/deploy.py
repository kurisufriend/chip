import os, json, sys

manifest = []

# install required packages (idempotent by default)
pkgs = [
    "hostname", # preinstalled on deb
    "cd-discid",
    "setcd",
    "whipper",
    "python3", # preinstalled on deb
    "python3-websockets",
    "sshfs",
    "curl",
    "beep"
]
manifest.append("apt update")
manifest.append("apt install -y " + " ".join(pkgs))


# add sshfs mount to <strike>/etc/fstab</strike> crontab

manifest.append("mkdir -p /mnt/chip")
# idempotent as heck
manifest.append("(echo \\\"@reboot sshfs /mnt/chip/ chip@alexandria.wuvt.vt.edu:/tank/archive/rips/chip -o IdentityFile=/root/.ssh/$$$HOSTNAME$$$-whoreslayer-node\\\") | crontab -")
manifest.append("(crontab -l; echo \\\"*/1 * * * * [ -d /mnt/chip/tools ] || sshfs /mnt/chip/ chip@alexandria.wuvt.vt.edu:/tank/archive/rips/chip -o IdentityFile=/root/.ssh/$$$HOSTNAME$$$-whoreslayer-node\\\") | crontab -")

# install systemd service (re-installs every time: idempotent by default)
link = "https://raw.githubusercontent.com/kurisufriend/chip/refs/heads/master/tools/service/chip-client.service"
manifest.append(f"curl {link} > /etc/systemd/system/chip-client.service")
manifest.append("systemctl daemon-reload")
manifest.append("systemctl enable chip-client.service")
manifest.append("systemctl start chip-client.service")



with open("nodes.json", "r") as f:
    nodes = json.loads(f.read())
    for n in nodes:
        if "--specify" in sys.argv and not n["host"] in sys.argv:
            continue
        for cmd in manifest:
            print(">> " + cmd)
            os.system(f"ssh root@{n['ipv4']} \"{cmd}\"".replace("$$$HOSTNAME$$$", n["host"]))