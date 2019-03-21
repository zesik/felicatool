# -*- coding: utf-8 -*-
from flask import Flask
from flask_socketio import SocketIO

from events import SocketIOEventHandler, StatusUpdater

NAMESPACE = '/felica'

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'secret!'

    from .views import main as main_blueprint
    app.register_blueprint(main_blueprint)

    socketio = SocketIO(async_mode='eventlet')
    socketio.init_app(app)

    updater = StatusUpdater(socketio, NAMESPACE)
    handler = SocketIOEventHandler(updater, NAMESPACE)
    socketio.on_namespace(handler)

    return app, socketio, updater
