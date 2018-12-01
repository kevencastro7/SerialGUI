# -*- coding: utf-8 -*-
"""
    pyfase
    Is a Fast-Asynchronous-microService-Environment based on ZeroMQ.
    :copyright: (c) 2016 by Joaci Morais.
"""

__author__ = 'Joaci Morais'

try:
    import os
    import sys
    import signal
    import inspect
    import zmq
    from threading import Thread
    from json import loads, dumps
except Exception as requirement_exception:
    print('requirements exception: %s' % requirement_exception)
    exit(0)


class Fase(object):
    __slots__ = ('ctx', 'receiver', 'sender')

    def __init__(self, sender_endpoint, receiver_endpoint):
        self.ctx = zmq.Context()
        self.receiver = self.ctx.socket(zmq.PULL)
        self.receiver.bind(receiver_endpoint)
        self.sender = self.ctx.socket(zmq.PUB)
        self.sender.bind(sender_endpoint)

    def execute(self):
        try:
            while True:
                self.sender.send_string(self.receiver.recv_string(), zmq.NOBLOCK)
        except Exception and KeyboardInterrupt:
            os.kill(os.getpid(), signal.SIGKILL)


class MicroService(object):
    __slots__ = ('name', 'log', 'actions', 'tasks', 'ctx', 'sender', 'receiver', 'o_pkg', 'action_context')

    def __init__(self, service, sender_endpoint, receiver_endpoint):
        if inspect.isclass(type(service)):
            self.name = service.__class__.__name__
            self.actions = {}
            self.tasks = {}
            self.ctx = zmq.Context()
            self.sender = self.ctx.socket(zmq.PUSH)
            self.sender.connect(receiver_endpoint)
            self.receiver = self.ctx.socket(zmq.SUB)
            self.receiver.connect(sender_endpoint)
            self.o_pkg = {}
            self.action_context = False
            """ filter <r> packages: Notify when a new Micro-Service is available """
            self.receiver.setsockopt_string(zmq.SUBSCRIBE, u'<r>:')
            """ filter <b> packages: Broadcast packages  """
            self.receiver.setsockopt_string(zmq.SUBSCRIBE, u'<b>:')
            """ filter response packages: Notify when receive an response from an action previous requested """
            self.receiver.setsockopt_string(zmq.SUBSCRIBE, u'%s:' % self.name)
            for name, func in service.__class__.__dict__.items():
                if hasattr(func, '__call__'):  # IS A FUNCTION?
                    if '_action_wrapper_' in func.__name__:  # IS AN ACTION?
                        self.actions[name] = func
                        """ filter only actions defined on this Micro-Service """
                        self.receiver.setsockopt_string(zmq.SUBSCRIBE, u'%s:' % name)
                    elif '_task_wrapper_' in func.__name__:  # IS A TASK?
                        self.tasks[name] = func
        else:
            raise Exception('MicroService %s must be a class' % service)

    @staticmethod
    def action(function):
        def _action_wrapper_(*args, **kwargs):
            return function(*args, **kwargs)
        return _action_wrapper_

    @staticmethod
    def task(function):
        def _task_wrapper_(*args, **kwargs):
            return function(*args, **kwargs)
        return _task_wrapper_

    @staticmethod
    def exit():
        os.kill(os.getpid(), signal.SIGKILL)

    def on_connect(self):
        pass

    def on_broadcast(self, service, data):
        pass

    def on_new_service(self, service, actions):
        pass

    def on_response(self, service, data):
        pass

    def start_task(self, task_name, data):
        if task_name in self.tasks:
            Thread(target=self.tasks[task_name], name=task_name, args=data).start()
        else:
            print('start_task: unknown task: %s' % task_name)

    def send_broadcast(self, data):
        self.sender.send_string('<b>:%s' % dumps({'s': self.name, 'd': data}), zmq.NOBLOCK)

    def request_action(self, action, data):
        self.sender.send_string('%s:%s' % (action, dumps({'s': self.name, 'd': data})), zmq.NOBLOCK)

    def response(self, data):
        if self.action_context:
            self.sender.send_string('%s:%s' % (self.o_pkg['s'], dumps({'s': self.name, 'd': data})), zmq.NOBLOCK)

    def execute(self, enable_tasks=None):
        try:
            if enable_tasks:
                for name, task in self.tasks.items():
                    Thread(target=task, name=name, args=(self,)).start()
            self.sender.send_string('<r>:%s' % dumps({'s': self.name,
                                                      'a': [action for action in self.actions]}), zmq.NOBLOCK)
            while True:
                pkg = self.receiver.recv_string()
                if '<r>:' in pkg:  # IS A REGISTER PACKAGE!
                    self.o_pkg = loads(pkg[4:])
                    service = self.o_pkg['s']
                    if self.name == service:
                        self.on_connect()
                    else:
                        self.on_new_service(service, self.o_pkg['a'])
                elif '<b>:' in pkg:  # IS A BROADCAST PACKAGE!
                    self.o_pkg = loads(pkg[4:])
                    service = self.o_pkg['s']
                    if self.name != service:
                        self.on_broadcast(service, self.o_pkg['d'])
                elif '%s:' % self.name in pkg:  # IS A RESPONSE PACKAGE!
                    pos = pkg.find(':')
                    self.o_pkg = loads(pkg[pos+1:])
                    self.on_response(self.o_pkg['s'], self.o_pkg['d'])
                else:  # IS AN ACTION PACKAGE!
                    pos = pkg.find(':')
                    self.o_pkg = loads(pkg[pos+1:])
                    self.action_context = True
                    self.actions[pkg[:pos]](self, self.o_pkg['s'], self.o_pkg['d'])
                    self.action_context = False
        except Exception and KeyboardInterrupt as execute_exception:
            print('execute exception: %s' % execute_exception)
            os.kill(os.getpid(), signal.SIGKILL)
