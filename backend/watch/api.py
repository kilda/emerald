import json
import logging
import sys
from typing import Optional

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

logging.basicConfig(stream=sys.stdout, level='INFO')

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
    expected_state: Optional[int]
    expected_state_path: str

class Global(BaseModel):
    color: str
    signal: str
    version: str

class Path(BaseModel):
    path: str
    value: str


async def process_request(payload):
    await req_sock.send(b'', zmq.SNDMORE)
    await req_sock.send_json(payload)
    message = await req_sock.recv_multipart()
    resp = json.loads(message[1])
    return resp


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
    req_sock = ctx.socket(zmq.DEALER)
    req_sock.bind('tcp://*:6667')

    global sub_sock
    sub_sock = ctx.socket(zmq.SUB)

    sub_sock.connect("tcp://localhost:6666")
    sub_sock.setsockopt(zmq.SUBSCRIBE, b'')


@app.post('/path')
async def read_for_path(path: Path):
    return await process_request({'type': 'get_path', 'path': path.path})


@app.put('/path')
async def update_for_path(path: Path):
    return await process_request({'type': 'set_path', 'path': path.path,
                                  'value': path.value})


@app.get('/components/{component}/{env}')
async def get_component(component: str, env: str):
    return await process_request({'type': 'get_component',
                                  'component': component, 'env': env})


@app.post('/global')
async def update_global(obj: Global):
    await process_request({'type': 'update_global',
                                   'global': vars(obj)})
    return 202

@app.post('/components')
async def update_component(obj: Component):
    return await process_request({'type': 'update_component',
                                  'component': vars(obj)})


@app.get('/components')
async def get_components():
    return await process_request({'type': 'components'})


@app.get("/")
async def redirect():
    response = RedirectResponse(url='/index.html')
    return response


app.mount("/", StaticFiles(directory="build"), name="build")

if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=1090)
