#!/usr/bin/env python
import eventlet
eventlet.monkey_patch()

import logging
import time

from app import create_app
from felica import Worker

def main():
    lvl = logging.INFO
    fmt = '%(asctime)s [%(threadName)s][%(name)s] %(levelname)s - %(message)s'
    formatter = logging.Formatter(fmt)
    formatter.converter = time.gmtime

    ch = logging.StreamHandler()
    ch.setLevel(lvl)
    ch.setFormatter(formatter)

    logging.getLogger().addHandler(ch)
    logging.getLogger().setLevel(logging.NOTSET)

    app, socketio, updater = create_app()

    worker = Worker(updater)
    worker.start()

    socketio.run(app, debug=True, use_reloader=False)

if __name__ == '__main__':
    main()
