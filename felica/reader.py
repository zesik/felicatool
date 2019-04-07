# -*- coding: utf-8 -*-
import errno
import logging
import io
import itertools
import nfc
import os
import threading
import time

from config import Config
from .record import BalanceRecord, HistoryRecord

FELICA_SERVICE_BALANCE = 0x008b
FELICA_SERVICE_HISTORY = 0x090f
FELICA_SERVICE_IN_OUT = 0x108f
BUFFER_SIZE = 1024

log = logging.getLogger('felica.reader')

def pairwise(iterable):
    a, b = itertools.tee(iterable)
    next(b, None)
    return zip(a, b)

class FelicaReader(object):
    def __init__(self, updater):
        self.updater = updater

    def _get_history_records_file(self, tagid):
        if not os.path.exists(Config.FELICA_HISTORY_RECORD_PATH):
            try:
                os.makedirs(Config.FELICA_HISTORY_RECORD_PATH)
            except Exception as e:
                log.error('error creating history record directory: %s', e)
        return os.path.join(Config.FELICA_HISTORY_RECORD_PATH, tagid)

    def _read_block(self, tag, service_code, block_code):
        sc = nfc.tag.tt3.ServiceCode(service_code >> 6, service_code & 0x3f)
        bc = nfc.tag.tt3.BlockCode(block_code)
        return tag.read_without_encryption([sc], [bc])

    def _read_all_blocks(self, tag, service_code):
        result = []
        for i in itertools.count():
            try:
                result.append(self._read_block(tag, service_code, i))
            except nfc.tag.tt3.Type3TagCommandError:
                break
            except Exception:
                raise
        return result

    def _tail(self, f, lines=5):
        if lines == 0:
            return []

        f.seek(0, io.SEEK_END)
        pos = f.tell()
        size = lines + 1
        block = -1
        data = []
        while size > 0 and pos > 0:
            if pos - BUFFER_SIZE > 0:
                f.seek(block * BUFFER_SIZE, io.SEEK_END)
                data.insert(0, f.read(BUFFER_SIZE))
            else:
                f.seek(0, io.SEEK_SET)
                data.insert(0, f.read(pos))
            lines_found = data[0].count('\n')
            size -= lines_found
            pos -= BUFFER_SIZE
            block -= 1
        return ''.join(data).splitlines()[-lines:]

    def _store_records(self, filename, raw_records):
        records = [' '.join(['{:02x}'.format(c) for c in r]) for r in raw_records]

        lines = []
        if os.path.exists(filename):
            try:
                with open(filename, 'rb') as f:
                    lines = self._tail(f, len(records) + 1)
            except Exception as e:
                log.error('error while open local file: %s', e)
                return (None, None)
        else:
            log.warn('local file does not exist')

        new_record_count = len(records)
        if lines:
            last_stored_record = lines[-1]
            for record in records:
                new_record_count -= 1
                if last_stored_record == record:
                    break
            else:
                new_record_count = len(records)

        if new_record_count == 0:
            log.info('no new records found')
        else:
            log.info('storing %d new record(s)', new_record_count)
            try:
                with open(filename, 'a') as f:
                    if new_record_count == len(records):
                        log.info('stored records and felica records not continuous')
                        f.write('\n')

                    for record in records[-new_record_count:]:
                        f.write('{}\n'.format(record))
            except Exception as e:
                log.error('error while storing records: %s', e)
                return (None, None)

        prev = None
        if new_record_count != len(records):
            prev_index = len(lines) - (len(records) - new_record_count) - 1
            if prev_index >= 0 and lines[prev_index]:
                prev = ''.join([chr(int(b, base=16)) for b in lines[prev_index].split(' ')])

        return (new_record_count, prev)

    def on_connected(self, tag):
        tagid = tag.identifier.encode("hex").lower()
        log.info('found tag: type=%s (\'%s\'), id=%s', tag.type, tag.product, tagid)
        self.updater.emit_status('読み込み中')

        if not isinstance(tag, nfc.tag.tt3.Type3Tag):
            log.error('cannot read data because tag is not Type3Tag')
            self.updater.emit_status('このカードは FeliCa カードではありませんでした')
            return

        try:
            raw_balance_records = self._read_all_blocks(tag, FELICA_SERVICE_BALANCE)
            if not raw_balance_records:
                raise Exception('not a Japan transportation card')
            raw_history_records = filter(lambda d: d[0], reversed(self._read_all_blocks(tag, FELICA_SERVICE_HISTORY)))
        except Exception as e:
            log.error('error while reading data: %s', e)
            self.updater.emit_status('交通系 IC カードとして読み込めませんでした')
            return

        new_record_count, prev = self._store_records(self._get_history_records_file(tagid), raw_history_records)
        history_records = map(lambda data: HistoryRecord(bytes(data)), raw_history_records)
        if new_record_count:
            for r in history_records[-new_record_count:]:
                r.new = True
        if prev:
            history_records.insert(0, HistoryRecord(bytes(prev)))
        for r1, r2 in pairwise(history_records):
            r2.expense = r1.balance - r2.balance
        if prev:
            history_records.pop(0)

        data = {
            'idm': tagid,
            'balance': BalanceRecord(raw_balance_records[0]).balance,
            'history': map(lambda record: record.to_dict(), history_records)
        }

        self.updater.emit_data(data)
        self.updater.emit_status('データを読み込みました')

    def run_once(self):
        device = ['usb']

        for path in device:
            try:
                log.info('searching contactless reader on %s', path)
                clf = nfc.ContactlessFrontend(path)
            except IOError as error:
                if error.errno == errno.ENODEV:
                    log.error('no contactless reader found on %s', path)
                elif error.errno == errno.EACCES:
                    log.error('access denied for device on %s', path)
                elif error.errno == errno.EBUSY:
                    log.error('the reader on %s is busy', path)
                else:
                    log.error('error while trying %s: %s', path, repr(error))
            else:
                log.debug('found a usable reader on %s', path)
                break
        else:
            log.error('no contactless reader available')
            self.updater.emit_status('カードリーダーを接続してください', {
                'product': "なし",
                'path': None
            })
            return False

        log.info('using %s', str(clf.device))
        self.updater.emit_status('カードをかざしてください', {
            'product': ' '.join(filter(bool, (clf.device.vendor_name, clf.device.product_name, clf.device.chipset_name))),
            'path': clf.device.path
        })

        try:
            return clf.connect(rdwr={'on-connect': self.on_connected})
        finally:
            clf.close()

    def run(self):
        while True:
            self.run_once()
            log.debug('wait for a while')
            time.sleep(5)
            log.info('starting over')
