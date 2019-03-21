# -*- coding: utf-8 -*-
import logging
import os

class Config(object):
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    LISTEN_HOST = 'localhost'
    LISTEN_PORT = 5000

    STATION_DATA_FILE = os.environ.get('STATION_DATA_FILE', os.path.join(BASE_DIR, '.data', 'station.csv'))
    FELICA_HISTORY_RECORD_PATH = os.environ.get('FELICA_HISTORY_RECORD_PATH', os.path.join(BASE_DIR, '.history'))
