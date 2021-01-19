import json
import logging
import sys

import uvicorn
import zmq
from fastapi import FastAPI
from fastapi import Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse
from starlette.responses import RedirectResponse
from zmq.asyncio import Context
from typing import Optional


logging.basicConfig(stream=sys.stdout, level='DEBUG')

req_sock = None
sub_sock = None

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)
logger = logging.getLogger('api')

class Component(BaseModel):
    service: str
    color: str
    signal: str
    signal_path: str
    state: Optional[int]
    state_path: str
    version: str
    version_path: str


class Path(BaseModel):
    path: str
    value: str

@app.get('/stream')
async def message_stream(request: Request):
    async def event_generator():
        while True:
            # If client was closed the connection
            if await request.is_disconnected():
                logger.info('sse connection is closed')
                break

            # Checks for new messages and return them to client if any
            msg = await sub_sock.recv_json()
            logger.info('received new update', msg)
            if msg:
                yield {
                    "data": json.dumps(msg)
                }

    return EventSourceResponse(event_generator())


@app.on_event('startup')
async def startup_event():
    global req_sock
    ctx = Context.instance()
    req_sock = ctx.socket(zmq.REQ)
    req_sock.connect('tcp://localhost:6667')

    global sub_sock
    sub_sock = ctx.socket(zmq.SUB)

    sub_sock.connect("tcp://localhost:6666")
    sub_sock.setsockopt(zmq.SUBSCRIBE, b'')


@app.post('/path')
async def read_for_path(path: Path):
    await req_sock.send_json({'type': 'get_path', 'path': path.path})
    message = await req_sock.recv_json()
    return message


@app.put('/path')
async def update_for_path(path: Path):
    await req_sock.send_json({'type': 'set_path', 'path': path.path,
                              'value': path.value})
    message = await req_sock.recv_json()
    return message


@app.get('/components/{component}/{env}')
async def get_component(component: str, env: str):
    await req_sock.send_json({'type': 'get_component',
                              'component': component, 'env': env})
    message = await req_sock.recv_json()
    return message


@app.post('/components')
async def update_component(obj: Component):
    await req_sock.send_json({'type': 'update_component',
                              'component': vars(obj)})
    message = await req_sock.recv_json()
    return message


@app.get('/components')
async def get_components():
    await req_sock.send_json({'type': 'components'})
    message = await req_sock.recv_json()
    return message


@app.get("/")
async def redirect():
    response = RedirectResponse(url='/index.html')
    return response


app.mount("/", StaticFiles(directory="build"), name="build")

if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=8080)
