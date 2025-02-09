#!/usr/bin/env python3
"""
important: working dir should be the repo root 

this is a wrapper for whipper 0.10.0, slaving the box it's running on to a cluster
    master for CD-ripping purposes. it's operation goes a little something like:
        - the script verifies that a whipper config is installed (with the drive offset)
            - if not, it pulls one down appropriate for the hardware in the cluster.
        - it connects to the master over ws and sends the checkin
        - event loop, update master on state change (tray open/closed/diskinfo)
        - if the tray is ever closed with nothing in it, open the tray
        - if the tray has a disk in it, and it's already ripped, open it
        - if it has a disk that hasn't begun ripping, indicate that fewise
            - if it is instructed to start ripping, generate a barcpde
            - if it is doubleinstructed to start ripping, rip
        - parse incoming live output from the ripping client into a status
           appropriate for display
        - be a winrar

barcodes:
    the software generates a barcode for every rip, before that rip starts.
    users should, after inserting the disk and requesting a code but before ripping,
    note this down on the case it came from. for inventory reasons, or something.
    the studio has a label roll that would serve well for this purpose

spec:
    transport: json over ws
    {"type": $type, "data": $data}

    + client -> serb

    {"type": "checkin/client", "data": {
        "hostname": $host,
        "meta": $meta;<random bullshit, str>
        "diskinfo": $diskinfo;<see diskinfo message type>}}
    
    {"type": "diskinfo", "data": {
        "open": $open;<full/empty/open>,
        "title": $title;<title of currently inserted disk>}}
    
    {"type": "liverip", "data": {"stdout": $stdout, "stderr": $stderr}}

    + serb -> client

    {"type": "eject", "data": {}}

    {"type": "rip", "data": {}}

    {"type": "error", "data": {"message": $err}}

    + fe -> serb

    {"type": "checkin/fe", "data": {}}

    + serb -> fe

    {"type": "state", "data": {
        "nodes": [
            {"hostname": $nHost,
            "diskinfo": $diskinfo;<see above>},
            ...
            ]}}

deployment:
    in theory:
        run master as an nfs mount. or sshfs. or whatever. load ./nodes.json or ansible hosts file with slave info.
        l8r: bother emachine about using alexandria for this instead like a sane person.
        ssh into each of the boxes, mount the rips/ root in the homedir of whatever acc i
         wrote down in the studio for these boxes and can't remember atm (hope nobody threw
          that sheet away L M A O  R  O  F  L   R   I   F   K), install a systemd service that
           starts the client (on the slave boxes), actually start said service, kick back & relax.
        
        atm im using my homedir on vtluug infra, ~/repos/chip. rips dir is ~/repos/chip/ripz/
        
        IGNORE THIS OLD IDEA:
            in the mounted rips/ dir:
                /chip, this repo
                /files, the location to actually rip to
                /barcode.txt, the current barcode increment

    in practice:
        ignore:
            set up the mount dir by hand. u can do it i habeeb in u.
        ignore:
            run ./deploy.sh to enact ghettoansible order 69 (mount on all teh boxes)
        ansible. just read the ansible dir.

~rsk (rishik@vt.edu [rsk@vtluug.org {rsk@wuvt.vt.edu <rishi@krishnas.club>}])
"""

import requests, subprocess, os, urllib, websockets, time, hashlib, json, asyncio

if not os.path.exists("/mnt/chip/tools"):
    print("mount not active, sleeping 10s...")
    time.sleep(10)


def get_drive_status():
    stat = subprocess.run("setcd -i /dev/sr0", shell=True, capture_output=True, text=True)
    stat = stat.stdout
    #print(stat, "found in drive" in stat)
    if "found in drive" in stat: return "full"
    elif "No disc" in stat: return "empty"
    elif "is open" in stat: return "open"
    else: return "ERR"

def drive_open(): subprocess.run("eject", shell=True)
def drive_close(): subprocess.run("eject -t", shell=True)

def disk_id():
    if get_drive_status() != "full":
        return "N/A"
    stat = subprocess.check_output("cd-discid /dev/sr0", shell=True)
    h = hashlib.shake_256(stat).hexdigest(3).upper()
    return f"{h[0:3]}-{h[3:]}"

def diskinfo():
    return {"type": "diskinfo", "data": {"open": get_drive_status(), "title": disk_id()}}

async def rip():
    cmd = ["whipper", "cd", "rip", "-O", "/mnt/chip/ripz/" + disk_id()]
    process = await asyncio.create_subprocess_exec(*cmd, stdout=asyncio.subprocess.PIPE)

    acc = ""
    while not process.stdout.at_eof():
        newc = await process.stdout.read(1)
        time.sleep(.01)
        if not newc:
            break
        acc += newc.decode("latin-1")
        if "\r" in acc:
            print(acc)
            acc = ""
            await ws.send(json.dumps({"type": "liverip", "data": {"stdout": acc, "stderr": ""}}))



# pull chip cfg
with open("/mnt/chip/cfg.json", "r") as f:
    cfg = json.loads(f.read())

# assert whipper cfg exists
if not os.path.exists("/root/.config/whipper/whipper.conf"):
    os.makedirs("/root/.config/whipper", exist_ok=True)
    urllib.request.urlretrieve("https://raw.githubusercontent.com/kurisufriend/chip/refs/heads/master/tools/whipper/whipper.conf")


# event loop
async def fuck():
    # checkin
    ws = await websockets.connect("ws://"+cfg["master-fqdn"]+":"+str(cfg["master-ws-port"]), ping_timeout=30, close_timeout=40)
    hostname = subprocess.check_output("hostname", shell=True).decode("latin-1").strip()
    await ws.send(json.dumps({"type": "checkin/client", "data": {
        "hostname": hostname,
        "meta": "",
        "diskinfo": diskinfo()
    }}))
    print("semt")
    while True:
        time.sleep(1)
        print("not blocking " + time.ctime())
        # tray closed w nothing in
        if get_drive_status() == "empty":
            drive_open()
            continue
        elif get_drive_status() == "open": continue
        
        # => we full
        did = disk_id()

        # if it's ripped already eject & fuck off
        if os.path.isdir("/mnt/chip/ripz/" + did):
            drive_open()
            continue

        # => we got an unripped disk. 

        await ws.send(json.dumps(diskinfo()))
        #await rip()
    await ws.close()

asyncio.run(fuck())

