# -*- coding: utf-8 -*-
import threading

class StatusUpdater(object):
    def __init__(self, socketio, namespace=None):
        self.socketio = socketio
        self.namespace = namespace
        self.status_lock = threading.Lock()
        self.status = None
        self.device = None

    def _emit_event(self, event, data, method=None):
        if not method:
            method = self.socketio.emit
        method(event, data, json=True, namespace=self.namespace)
        self.socketio.sleep(0)

    def emit_status(self, status=None, device=None, method=None):
        with self.status_lock:
            if status:
                self.status = status
            if device:
                self.device = device
            status = self.status
            device = self.device
        data = { 'device': device, 'status': status }
        self._emit_event('hardware', data, method)

    def emit_data(self, data, method=None):
        self._emit_event('felica', data, method)
