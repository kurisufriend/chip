import websockets, json, threading, asyncio, time

class serb():
    def __init__(self, config_path = "cfg.json"):
        self.clients = {}
        with open(config_path) as f:
            self.config = json.loads(f.read())
        self.fes = {}

    async def run(self):
        asyncio.get_event_loop().create_task(self.update_fes())
        async with websockets.serve(self.ws_handler, "", self.config["master-ws-port"]):
            await asyncio.get_running_loop().create_future()

    async def ws_handler(self, ws):
        while True:
            try: msg = await ws.recv()
            except:
                try: self.clients.pop(ws.remote_address)
                except: pass
                try: self.fes.pop(ws.remote_address)
                except: pass
                break


            try: j = json.loads(msg)
            except:
                await ws.send(json.dumps(
                    {"type": "error", "data": {"message": "could not deserialize!"}}
                ))
                continue
            print("wsh_"+j["type"].replace("/", "_"))

            if j.get("type") == None or j.get("data") == None:
                await ws.send(json.dumps(
                    {"type": "error", "data": {"message": "missing required field(s) type and/or data!"}}
                ))
                continue

            if self.clients.get(ws.remote_address) == None and not j.get("type").startswith("checkin/"):
                await ws.send(json.dumps(
                    {"type": "error", "data": {"message": "clients must first check in!"}}
                ))
                continue
            

            handler = getattr(self, "wsh_"+j["type"].replace("/", "_"), None)
            try: await handler(ws, j)
            except TypeError:
                print("unhandled ws message:", msg)
            except Exception as e:
                print("error while processing ws message", msg, e)
                await ws.send(self._helper_ws_msg("error", "error while processing command"+msg+e))
                await ws.close(1002)
                try: self.clients.pop(ws.remote_address)
                except: pass
                try: self.fes.pop(ws.remote_address)
                except: pass
                return

            print(self.fes)
            if self.clients.get(ws.remote_address) is None and self.fes.get(ws.remote_address) is not None:
                print("new FE")
                continue

            print(time.ctime() + " // FROM " + self.clients[ws.remote_address]["hostname"] + json.dumps(j, indent=2))

    async def wsh_checkin_client(self, ws, message):
        self.clients[ws.remote_address] = {"hostname": message["data"]["hostname"]}
        self.clients[ws.remote_address]["diskinfo"] = message["data"]["diskinfo"]
        self.clients[ws.remote_address]["ws"] = ws
        self.clients[ws.remote_address]["ripstatus"] = "..."

    async def wsh_checkin_fe(self, ws, message):
        self.fes[ws.remote_address] = {"yay": "louder", "ws": ws}
        
    async def wsh_diskinfo(self, ws, message):
        self.clients[ws.remote_address]["diskinfo"] = message
        
    async def wsh_liverip(self, ws, message):
        self.clients[ws.remote_address]["ripstatus"] = message
    
    async def update_fes(self):
        while True:
            await asyncio.sleep(1)
            package = {"type": "state", "data": []}
            for clientk in self.clients:
                client = self.clients[clientk]
                res = {
                    "hostname": client["hostname"],
                    "diskinfo": client["diskinfo"],
                    "ripstatus": client["ripstatus"],
                }
                package["data"].append(res)
            for fek in self.fes.keys():
                fe = self.fes[fek]
                await fe["ws"].send(json.dumps(package))


serber = serb()

asyncio.run(serber.run())