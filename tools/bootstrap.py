# working dir should be repo root

import os, sys, subprocess


if not os.getenv("CHIP_PASS"):
    print("CHIP_PASS environment variable must be set the the password of the `chip` service user on alexandria")
    print("try something like\nexport CHIP_PASS=\"passwd goes here\" && python3 tools/bootstrap.py")
    sys.exit(1)

# run as root
if subprocess.check_output(["whoami"]).decode("ascii").replace("\n", "") != "root":
    print("run as root")
    sys.exit(2)


# install our keys
os.system("mkdir -p /root/.ssh")
os.system("echo \"\" > /root/.ssh/authorized_keys")
for k in os.listdir("tools/keys"):
    if not k.endswith(".pub"): continue
    os.system(f"cat tools/keys/{k} >> /root/.ssh/authorized_keys")


def notsed(file, old, new):
    with open(file, "r") as fr:
        with open(file, "w") as fw:
            fw.write(fr.read().replace(old, new))

# enable root ssh
notsed("/etc/ssh/sshd_config", "#PermitRootLogin prohibit-password", "PermitRootLogin prohibit-password")

# disable password auth
notsed("/etc/ssh/sshd_config", "#PasswordAuthentication yes", "PasswordAuthentication no")
notsed("/etc/ssh/sshd_config", "#PubkeyAuthentication yes", "PubkeyAuthentication yes")

os.system("systemctl restart sshd")


# fetch chip/alexandria keypair
os.system("scp chip@alexandria.wuvt.vt.edu:/opt/chip/.ssh/chip-shared* /root/.ssh/")

# clear bash_history to minimize cred leakage
os.system("rm /root/.bash_history")