# -*- coding: utf-8 -*-
import logging
import threading

from .reader import FelicaReader

log = logging.getLogger('felica.worker')

class Worker(threading.Thread):
    def __init__(self, updater):
        super(Worker, self).__init__()
        self.updater = updater

    def run(self):
        log.info('worker thread started')
        reader = FelicaReader(self.updater)
        reader.run()
        log.info('worker thread exiting')
