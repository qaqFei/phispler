import init_logging as _

import webcv
import asyncio
import random
import threading
import websockets
import json
import logging

import utils

def start_server(window: webcv.WebCanvas, addr: str, port: int):
    client = utils.ValueEvent()
    tasks: dict[int, utils.ValueEvent] = {}
    
    async def main_logic(ws: websockets.WebSocketServerProtocol, path: str):
        nonlocal client
        client.set(ws)
        
        while True:
            recv = await ws.recv()
            data = json.loads(recv)
            
            match data["type"]:
                case "evaljs_result":
                    tasks[data["tid"]].set(data.get("result", None))
                
                case "jsapi_callback":
                    window.jsapi.call_attr(data["name"], *data["args"])
            
    sendlock = threading.Lock()
    
    def evaljs(
        code: str,
        needresult: bool = True,
        *args, **kwargs
    ):
        tid = random.randint(0, 2 << 31)
        tasks[tid] = utils.ValueEvent()
        
        protocol: websockets.WebSocketServerProtocol = client.wait()
        
        sendlock.acquire()
        asyncio.run(protocol.send(json.dumps({
            "type": "evaljs",
            "code": code,
            "tid": tid
        }, ensure_ascii=False)))
        sendlock.release()
        
        if needresult:
            return tasks[tid].wait()
    
    while True:
        try:
            try: loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
            server = websockets.serve(main_logic, addr, port, loop=loop)
            loop.run_until_complete(server)
            threading.Thread(target=loop.run_forever, daemon=True).start()
        except Exception as e:
            logging.error(f"start server on port {port} failed: {repr(e)}")
            if port > 65535:
                raise Exception("port out of range")
            port += 1
            continue
        break
    
    return evaljs

def hook(window: webcv.WebCanvas):
    window.evaljs = start_server(window, "", 8080)
