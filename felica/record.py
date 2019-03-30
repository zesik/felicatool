# -*- coding: utf-8 -*-
import csv
import datetime
import struct

from config import Config

# https://ja.osdn.net/projects/felicalib/wiki/suica
# https://www.wdic.org/w/RAIL/%E3%82%B5%E3%82%A4%E3%83%90%E3%83%8D%E8%A6%8F%E6%A0%BC%20%28IC%E3%82%AB%E3%83%BC%E3%83%89%29
# https://github.com/rfujita/libpafe-ruby/blob/master/sample/suica.rb

class StationRecord(object):
    db = None

    def __init__(self, row):
        self.key = (int(row[0], 10), int(row[1], 10), int(row[2], 10))
        self.company = row[3]
        self.line = row[4]
        self.station = row[5]

    def to_dict(self):
        return {
            'company': self.company,
            'line': self.line,
            'station': self.station
        }

    @classmethod
    def get_db(cls, filename):
        if not cls.db:
            cls.db = {}
            for row in csv.reader(open(filename, 'rU'), delimiter=',', dialect=csv.excel_tab):
                r = cls(row)
                cls.db[r.key] = r
        return cls.db

    @classmethod
    def get_station(cls, area, line, station):
        return cls.get_db(Config.STATION_DATA_FILE).get((area, line, station), None)

class Record(object):
    def __str__(self):
        if self.raw:
            return ''.join(['{:02x}'.format(ord(b)) for b in self.raw])

    @classmethod
    def get_date(cls, date):
        return datetime.date(
            (date >> 9) + 2000,
            (date >> 5) & 0x0f,
            date & 0x1f
        )

    @classmethod
    def get_time(cls, time):
        return datetime.time(
            time >> 11,
            (time >> 5) & 0x3f,
            (time & 0x1f) * 2
        )

    @classmethod
    def get_time_bcd(cls, time):
        return datetime.time(
            int('{:02x}'.format(time >> 8)),
            int('{:02x}'.format(time & 0xff))
        )

    @classmethod
    def format_date(cls, date):
        weekday = date.weekday()
        if weekday == 0:
            weekday_str = '(月)'
        elif weekday == 1:
            weekday_str = '(火)'
        elif weekday == 2:
            weekday_str = '(水)'
        elif weekday == 3:
            weekday_str = '(木)'
        elif weekday == 4:
            weekday_str = '(金)'
        elif weekday == 5:
            weekday_str = '(土)'
        elif weekday == 6:
            weekday_str = '(日)'
        return '{0:%Y年%m月%d日}{1}'.format(date, weekday_str)

class BalanceRecord(Record):
    def __init__(self, raw):
        self.raw = bytes(raw)
        self.data = struct.unpack('>IIBH3BH', self.raw)
        self.balance = self.data[4] | (self.data[5] << 8)

    def to_dict(self):
        return {
            'raw': str(self),
            'balance': self.balance,
        }

class HistoryRecord(Record):
    def __init__(self, raw):
        self.raw = bytes(raw)
        self.data = struct.unpack('>4BH7BHB', self.raw)
        self.terminal = self.get_terminal(self.data[0])
        self.process = self.get_process(self.data[1])
        self.date = self.get_date(self.data[4])
        self.time = None
        self.in_station = None
        self.out_station = None
        self.commuter_pass = None

        process = self.data[1] & 0x7f
        if self.is_format_time(process):
            self.time = self.get_time((self.data[5] << 8) | self.data[6])
        if self.is_format_in_station(process):
            self.in_station = StationRecord.get_station(self.data[13] >> 6, self.data[5], self.data[6])
        if self.is_format_out_station(process):
            self.out_station = StationRecord.get_station((self.data[13] & 0xf0) >> 4, self.data[7], self.data[8])
        if self.data[3] == 0x03:
            self.commuter_pass = 'in'
        elif self.data[3] == 0x04:
            self.commuter_pass = 'out'

        self.balance = self.data[9] | (self.data[10] << 8)
        self.serial = self.data[12]
        self.expense = None
        self.new = False

    def to_dict(self):
        return {
            'raw': str(self),
            'new': self.new,
            'terminal': self.terminal,
            'process': self.process,
            'date': self.format_date(self.date),
            'time': self.time.strftime('%H:%M:%S') if self.time else None,
            'in_station': self.in_station.to_dict() if self.in_station else None,
            'out_station': self.out_station.to_dict() if self.out_station else None,
            'commuter_pass': self.commuter_pass,
            'expense': self.expense,
            'balance': self.balance,
            'serial': self.serial
        }

    @classmethod
    def get_terminal(cls, key):
        return {
            0x03: 'のりこし精算機',
            0x05: 'バス・路面等',
            0x07: '券売機',
            0x08: '券売機',
            0x09: '入金機',
            0x12: '券売機',
            0x14: '窓口端末',
            0x15: '定期券発券機',
            0x16: '改札機',
            0x17: '簡易改札機',
            0x18: '窓口端末',
            0x19: '窓口端末',
            0x1a: '窓口端末',
            0x1b: 'パソリ等',
            0x1c: 'のりつぎ精算機',
            0x1d: 'のりかえ改札機',
            0x1f: '簡易入金機',
            0x20: '窓口端末',
            0x21: '精算機',
            0x23: '新幹線改札機',
            0x24: '車内補充券発行機',
            0x46: 'VIEW ALTTE',
            0x48: 'ポイント交換機',
            0xc7: '物販・タクシー',
            0xc8: '自販機'
        }.get(key, '0x{:02x}'.format(key))

    @classmethod
    def get_process(cls, key):
        return {
            0x01: '改札出場',
            0x02: 'チャージ',
            0x03: '乗車券購入',
            0x04: '精算',
            0x05: '入場精算',
            0x06: '窓口出場',
            0x07: '新規発行',
            0x08: '窓口控除',
            0x0c: 'バス・路面等',
            0x0d: 'バス・路面等',
            0x0f: 'バス・路面等',
            0x10: '再発行処理',
            0x11: '再発行処理',
            0x13: '新幹線改札出場',
            0x14: '入場時オートチャージ',
            0x15: '出場時オートチャージ',
            0x19: 'バス精算',
            0x1a: 'バス精算',
            0x1b: 'バス精算',
            0x1f: 'バスチャージ',
            0x23: 'バス・路面等企画券購入',
            0x33: '残高返金',
            0x46: '物販',
            0x48: 'ポイントチャージ',
            0x49: 'レジ入金',
            0x4a: '物販取消',
            0x4b: '入場物販'
        }.get(key & 0x7f, '0x{:02x}'.format(key))

    @classmethod
    def is_format_time(cls, key):
        return key in [0x46, 0x49, 0x4a, 0x4b]

    @classmethod
    def is_format_in_station(cls, key):
        return key in [0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08, 0x10, 0x11, 0x13, 0x14, 0x15, 0x33]

    @classmethod
    def is_format_out_station(cls, key):
        return key in [0x01, 0x03, 0x04, 0x05, 0x06, 0x13]
