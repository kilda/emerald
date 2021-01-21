import logging
import os
import sys
from functools import partial

import eventlet
from eventlet.green import zmq
from kazoo.client import KazooClient
from kazoo.handlers.eventlet import SequentialEventletHandler
from kazoo.protocol.states import EventType

logging.basicConfig(stream=sys.stdout, level='DEBUG')
logger = logging.getLogger('app')

ctx = zmq.Context()
pub_sock = ctx.socket(zmq.PUB)

pub_sock.bind("tcp://*:6666")

rep_sock = ctx.socket(zmq.REP)
rep_sock.bind("tcp://*:6667")
hosts = os.environ.get('ZK_HOSTS')
zk_root = os.environ.get('ZK_ROOT')
zk = KazooClient(hosts=hosts,
                 handler=SequentialEventletHandler())
zk.start()

paths_map = {}
component_map = {}
discovered_components = set()


class Component:
    def __init__(self, service, color, signal, signal_path, state,
                 state_path, version, version_path):
        self.service = service
        self.color = color
        self.signal = signal
        self.signal_path = signal_path
        self.state = state
        self.state_path = state_path
        self.version = version
        self.version_path = version_path

    def update_for_path(self, path, val):
        if path == self.signal_path:
            self.signal = val
        elif path == self.state_path:
            if val:
                val = int(val)
            self.state = val
        elif path == self.version_path:
            self.version = val

    def get_for_path(self, path):
        if path == self.signal_path:
            return self.signal
        elif path == self.state_path:
            return self.state
        elif path == self.version_path:
            return self.version


def my_callback(path, data, stat):
    try:
        logger.info('received %s for path %s', data, path)
        data = data.decode('utf-8')
        if path in paths_map:
            paths_map[path].update_for_path(path, data)
            pub_sock.send_json(vars(paths_map[path]))
    except Exception as e:
        logger.error(e)


def unit_children_callback(root, component, env, children, event):
    try:
        if event and event.type == EventType.CHILD:
            logger.info('received children update for path %s',
                        '/'.join([root, component, env]))
            discover_unit(root, component, env)
    except Exception as e:
        logger.error(e)


def component_children_callback(root, component, children, event):
    try:
        if event and event.type == EventType.CHILD:
            logger.info('received children update for path %s',
                        '/'.join([root, component]))
            discover_components(root, component)
    except Exception as e:
        logger.error(e)


def root_children_callback(root, children, event):
    try:
        if event and event.type == EventType.CHILD:
            logger.info('received children update for path %s',
                        root)
            get_states(root)
    except Exception as e:
        logger.error(e)


def handle_requests():
    while True:
        message = rep_sock.recv_json()
        m_type = message['type']
        if m_type == 'get_path':
            path = message['path']
            rep_sock.send_json({'path': path,
                                'data': paths_map[path].get_for_path(path)})
        elif m_type == 'set_path':
            path = message['path']
            new_val = str.encode(message['value'])
            zk.set_async(path, new_val)
            rep_sock.send_json({'path': path,
                                'success': True})
        elif m_type == 'get_component':
            comp = message['component']
            env = message['env']
            rep_sock.send_json(vars(component_map[(comp, env)]))
        elif m_type == 'update_component':
            comp = message['component']
            zk.set(comp['signal_path'], str.encode(comp['signal']))
            zk.set(comp['version_path'], str.encode(comp['version']))
            rep_sock.send_json({'path': comp['service'] + '/' + comp['color'],
                                'success': True})
        elif m_type == 'components':
            ans = []
            for v in component_map.values():
                ans.append((vars(v)))
            rep_sock.send_json(ans)


def get_paths(root=zk_root):
    children = zk.get_children(root)
    if children:
        for child in children:
            get_paths(root + '/' + child)
    else:
        zk.DataWatch(root, partial(my_callback, root))


def get_states(root=zk_root):
    zk.ChildrenWatch(root,
                     partial(root_children_callback, root),
                     send_event=True)
    children = zk.get_children(root)
    for component in children:
        if component not in discovered_components:
            discover_components(root, component)
            discovered_components.add(component)


def discover_components(root, component):
    zk.ChildrenWatch('/'.join([root, component]),
                     partial(component_children_callback, root, component),
                     send_event=True)
    envs = zk.get_children('/'.join([root, component]))
    for env in envs:
        discover_unit(root, component, env)


BUILD_VERSION = 'build-version'
SIGNAL = 'signal'
STATE = 'state'


def discover_unit(root, component, env):
    zk.ChildrenWatch('/'.join([root, component, env]),
                     partial(unit_children_callback, root, component, env),
                     send_event=True)
    build_version_path = '/'.join([root, component, env, BUILD_VERSION])
    build_version = None
    if zk.exists(build_version_path):
        build_version = zk.get(build_version_path)[0].decode('utf-8')
        zk.DataWatch(build_version_path, partial(my_callback,
                                                 build_version_path))

    signal_path = '/'.join([root, component, env, SIGNAL])
    signal = None
    if zk.exists(signal_path):
        signal = zk.get(signal_path)[0].decode('utf-8')
        zk.DataWatch(signal_path, partial(my_callback, signal_path))

    state_path = '/'.join([root, component, env, STATE])
    state = None
    if zk.exists(state_path):
        state = zk.get(state_path)[0].decode('utf-8')
        if state:
            state = int(state)
        zk.DataWatch(state_path, partial(my_callback, state_path))

    comp = Component(component, env, signal=signal,
                     signal_path=signal_path, state=state,
                     state_path=state_path, version=build_version,
                     version_path=build_version_path)
    paths_map[signal_path] = comp
    paths_map[state_path] = comp
    paths_map[build_version_path] = comp
    component_map[(component, env)] = comp


if __name__ == '__main__':
    get_states()
    eventlet.spawn(handle_requests)
    while True:
        eventlet.sleep(30)
