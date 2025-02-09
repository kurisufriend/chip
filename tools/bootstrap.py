# working dir should be repo root

import os, sys, subprocess


if not os.getenv("SSHPASS"):
    print("SSHPASS environment variable must be set the the password of the `chip` service user on alexandria")
    print("try something like\nexport SSHPASS=\"passwd goes here\" && python3 tools/bootstrap.py")
    sys.exit(1)

# run as root
if subprocess.check_output(["whoami"]).decode("ascii").replace("\n", "") != "root":
    print("run as root")
    sys.exit(2)


# install our keys
print("installing keys...")
os.system("mkdir -p /root/.ssh")
os.system("echo \"\" > /root/.ssh/authorized_keys")
for k in os.listdir("tools/keys"):
    if not k.endswith(".pub"): continue
    os.system(f"cat tools/keys/{k} >> /root/.ssh/authorized_keys")


def notsed(file, old, new):
    with open(file, "r") as fr:
        with open(file, "w") as fw:
            fw.write(fr.read().replace(old, new))

print("enabling root ssh & disabling password auth...")
# enable root ssh
notsed("/etc/ssh/sshd_config", "#PermitRootLogin prohibit-password", "PermitRootLogin prohibit-password")

# disable password auth
notsed("/etc/ssh/sshd_config", "#PasswordAuthentication yes", "PasswordAuthentication no")
notsed("/etc/ssh/sshd_config", "#PubkeyAuthentication yes", "PubkeyAuthentication yes")

os.system("systemctl restart sshd")


# install sshpass
os.system("apt install -y sshpass")

# generate new keys & copy to chip@alexandria
os.system("ssh-keygen -f /root/.ssh/$(hostname)-whoreslayer-node -t ed25519")
os.system("sshpass -e ssh-copy-id -i /root/.ssh/$(hostname)-whoreslayer-node chip@alexandria.wuvt.vt.edu")

# clear bash_history to minimize cred leakage
os.system("rm /root/.bash_history")