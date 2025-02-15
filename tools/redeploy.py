import os, json

manifest = []
manifest.append("systemctl restart chip-client.service")



with open("nodes.json", "r") as f:
    nodes = json.loads(f.read())
    print(nodes[0])
    runonce = f'ssh -i /root/.ssh/{nodes[0]["host"]}-whoreslayer-node chip@alexandria.wuvt.vt.edu \\"cd /tank/archive/rips/chip && git pull\\"'
    os.system(f"ssh root@{nodes[0]['ipv4']} \"{runonce}\"")
    for n in nodes:
        for cmd in manifest:
            print(n["host"] + ":" + cmd)
            os.system(f"ssh root@{n['ipv4']} \"{cmd}\"")