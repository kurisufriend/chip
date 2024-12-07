#!/usr/bin/env python3
"""
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
        "open": $open;true/false,
        "title": $title;<title of currently inserted disk>}}
    
    {"type": "liverip", "data": {"stdout": $stdout, "stderr": $stderr}}

    + serb -> client

    {"type": "eject", "data": {}}

    {"type": "rip", "data": {}}

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
        run master as an nfs mount. or sshfs. or whatever. load ./nodes.json with slave info.
        l8r: bother emachine about using alexandria for this instead like a sane person.
        ssh into each of the boxes, mount the rips/ root in the homedir of whatever acc i
         wrote down in the studio for these boxes and can't remember atm (hope nobody threw
          that sheet away L M A O  R  O  F  L   R   I   F   K), install a systemd service that
           starts the client (on the slave boxes), actually start said service, kick back & relax.
        
        in the mounted rips/ dir:
            /chip, this repo
            /files, the location to actually rip to
            /barcode.txt, the current barcode increment

    in practice:
        set up the mount dir by hand. u can do it i habeeb in u.
        run ./deploy.sh to enact ghettoansible order 69 (mount on all teh boxes)

~rsk (rishik@vt.edu [rsk@vtluug.org {rsk@wuvt.vt.edu <rishi@krishnas.club>}])
"""