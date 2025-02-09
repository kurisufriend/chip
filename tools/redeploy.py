import os, json

runonce = 'ssh chip@alexandria.wuvt.vt.edu \\"cd /tank/archive/rips/chip && git pull\\"'
manifest = []
manifest += "systemctl service restart chip-client.service"



with open("nodes.json", "r") as f:
    nodes = json.loads(f.read())
    print(nodes[0])
    os.system(f"ssh root@{nodes[0]['ipv4']} \"f{runonce}\"")
    for n in nodes:
        for cmd in manifest:
            os.system(f"ssh root@{n['ipv4']} \"f{cmd}\"")