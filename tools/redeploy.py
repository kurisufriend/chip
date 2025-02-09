import os

runonce = 'ssh chip@alexandria.wuvt.vt.edu "cd /tank/archive/rips/chip && git pull"'
manifest = []
manifest += "systemctl service restart chip-client.service"



with open("nodes.json", "r") as f:
    nodes = json.loads(f.read())
    for n in nodes:
        for cmd in manifest:
            os.system(f"ssh root@{n['ipv6']} \"f{cmd}\"")