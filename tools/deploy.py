import os, json

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
manifest.append("apt install -y " + " ".join(pkgs))


# add sshfs mount to /etc/fstab

manifest.append("mkdir -p /mnt/chip")
# idempotent as heck
manifest.append('grep -q "sshfs#chip@alexandria.wuvt.vt.edu" /etc/fstab || echo "sshfs#chip@alexandria.wuvt.vt.edu:/tank/archive/rips/chip /mnt/chip fuse.sshfs defaults,noatime,reconnect,allow_other,IdentityFile=/root/.ssh/chip-shared 0 0" >> /etc/fstab')
manifest.append("mount /mnt/chip")

# install systemd service (re-installs every time: idempotent by default)
link = "https://raw.githubusercontent.com/kurisufriend/chip/refs/heads/master/tools/service/chip-client.service"
manifest.append(f"curl {link} > /etc/systemd/system/chip-client.service")
manifest.append("systemctl daemon-reload")
manifest.append("systemctl enable chip-client.service")
manifest.append("systemctl start chip-client.service")



with open("nodes.json", "r") as f:
    nodes = json.loads(f.read())
    for n in nodes:
        for cmd in manifest:
            print(">> " + cmd)
            os.system(f"ssh root@{n['ipv4']} \"{cmd}\"")