# -*- coding: utf-8 -*-
from flask_socketio import Namespace, emit

class SocketIOEventHandler(Namespace):
    def __init__(self, updater, namespace=None):
        super(SocketIOEventHandler, self).__init__(namespace)
        self.updater = updater

    def on_connect(self):
        self.updater.emit_status(method=emit)

    def on_disconnect(self):
        pass
