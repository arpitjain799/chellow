import csv
import threading
import collections
import traceback
from dateutil.relativedelta import relativedelta
import requests
from chellow.models import (
    Session, Contract, RateScript, get_non_core_contract_id)
from chellow.utils import HH, hh_format, utc_datetime_now, to_utc, to_ct
from werkzeug.exceptions import BadRequest
import atexit
from datetime import datetime as Datetime
from decimal import Decimal, InvalidOperation
from sqlalchemy import or_
from sqlalchemy.sql.expression import null
from zish import loads, dumps


ELEXON_PORTAL_SCRIPTING_KEY_KEY = 'elexonportal_scripting_key'


def key_format(dt):
    return dt.strftime("%d %H:%M")


def hh(data_source, run='DF'):
    rate_set = data_source.supplier_rate_sets['tlm']
    gsp_group_code = data_source.gsp_group_code

    try:
        cache = data_source.caches['tlms']
    except KeyError:
        cache = data_source.caches['tlms'] = {}

    for h in data_source.hh_data:
        try:
            h['tlm'] = tlm = cache[h['start-date']][gsp_group_code][run]
        except KeyError:
            h_start = h['start-date']
            db_id = get_non_core_contract_id('tlms')
            rates = data_source.hh_rate(db_id, h_start)['tlms']

            key = key_format(h_start)
            try:
                rate = rates[key]
            except KeyError:
                rate = sorted(rates.items())[-1][1]

            try:
                gsp_rate = rate[gsp_group_code]
            except KeyError:
                gsp_rate = sorted(rate.items())[-1][1]

            try:
                h['tlm'] = tlm = float(gsp_rate[run]['off_taking'])
            except KeyError:
                h['tlm'] = tlm = float(
                    sorted(gsp_rate.items())[-1][1]['off_taking'])

            try:
                rates_cache = cache[h['start-date']]
            except KeyError:
                rates_cache = cache[h['start-date']] = {}

            try:
                gsp_cache = rates_cache[gsp_group_code]
            except KeyError:
                gsp_cache = rates_cache[gsp_group_code] = {}

            gsp_cache[run] = tlm

        rate_set.add(tlm)
        h['nbp-kwh'] = h['gsp-kwh'] * tlm


tlm_importer = None


class TlmImporter(threading.Thread):
    def __init__(self):
        super(TlmImporter, self).__init__(name="TLM Importer")
        self.lock = threading.RLock()
        self.messages = collections.deque(maxlen=100)
        self.stopped = threading.Event()
        self.going = threading.Event()
        self.PROXY_HOST_KEY = 'proxy.host'
        self.PROXY_PORT_KEY = 'proxy.port'

    def stop(self):
        self.stopped.set()
        self.going.set()
        self.join()

    def go(self):
        self.going.set()

    def is_locked(self):
        if self.lock.acquire(False):
            self.lock.release()
            return False
        else:
            return True

    def log(self, message):
        self.messages.appendleft(
            utc_datetime_now().strftime("%Y-%m-%d %H:%M:%S") + " - " + message)

    def run(self):
        while not self.stopped.isSet():
            if self.lock.acquire(False):
                sess = None
                caches = {}
                try:
                    sess = Session()
                    self.log("Starting to check TLMs.")
                    contract = Contract.get_non_core_by_name(sess, 'tlms')

                    config = Contract.get_non_core_by_name(
                        sess, 'configuration')
                    props = config.make_properties()

                    scripting_key = props.get(
                        ELEXON_PORTAL_SCRIPTING_KEY_KEY)
                    if scripting_key is None:
                        raise BadRequest(
                            "The property " +
                            ELEXON_PORTAL_SCRIPTING_KEY_KEY +
                            " cannot be found in the configuration " +
                            "properties.")

                    contract_props = contract.make_properties()
                    url_str = ''.join(
                        (
                            contract_props['url'],
                            'file/download/TLM_FILE?key=', scripting_key))

                    r = requests.get(url_str)
                    parser = csv.reader(
                        (l.decode() for l in r.iter_lines()),
                        delimiter=',', quotechar='"')
                    self.log("Opened " + url_str + ".")

                    next(parser, None)
                    for values in parser:
                        if values[3] == '':
                            for zone in GSP_GROUP_LOOKUP.keys():
                                values[3] = zone
                                _process_line(
                                    caches, sess, contract, self.log, values)
                        else:
                            _process_line(
                                caches, sess, contract, self.log, values)

                    self.log("Saving found rates.")
                    for yr in caches['tlms']['scripts'].values():
                        for rs, rates in yr.values():
                            rs.script = dumps(rates)
                    sess.commit()
                    self.log("Rates saved.")

                except BadRequest as e:
                    self.log("Problem: " + e.description)
                    sess.rollback()
                except BaseException:
                    self.log("Outer problem " + traceback.format_exc())
                    sess.rollback()
                finally:
                    if sess is not None:
                        sess.close()
                    self.lock.release()
                    self.log("Finished checking TLM rates.")

            self.going.wait(30 * 60)
            self.going.clear()


GSP_GROUP_LOOKUP = {
    '1': '_P',
    '2': '_N',
    '3': '_F',
    '4': '_G',
    '5': '_M',
    '6': '_D',
    '7': '_B',
    '8': '_E',
    '9': '_A',
    '10': '_K',
    '11': '_J',
    '12': '_C',
    '13': '_H',
    '14': '_L'}


def _process_line(caches, sess, contract, log_func, values):
    hh_date_ct = to_ct(Datetime.strptime(values[0], "%d/%m/%Y"))
    hh_date = to_utc(hh_date_ct)
    hh_date += relativedelta(minutes=30*(int(values[2]) - 1))
    run = values[1]
    gsp_group_code = GSP_GROUP_LOOKUP[values[3]]
    off_taking_str = values[4]

    try:
        off_taking = Decimal(off_taking_str)
    except InvalidOperation as e:
        raise BadRequest(
            "Problem parsing 'off-taking' field '" + off_taking_str +
            "' in the row " + str(values) + ". " + str(e))

    delivering = Decimal(values[5])

    try:
        rs, rates = caches['tlms']['scripts'][hh_date.year][hh_date.month]
    except KeyError:
        try:
            tlms_cache = caches['tlms']
        except KeyError:
            tlms_cache = caches['tlms'] = {}

        try:
            script_cache = tlms_cache['scripts']
        except KeyError:
            script_cache = tlms_cache['scripts'] = {}

        try:
            yr_cache = script_cache[hh_date.year]
        except KeyError:
            yr_cache = script_cache[hh_date.year] = {}

        rs = sess.query(RateScript).filter(
            RateScript.contract == contract,
            RateScript.start_date <= hh_date, or_(
                RateScript.finish_date == null(),
                RateScript.finish_date >= hh_date)).first()
        while rs is None:
            log_func("There's no rate script at " + hh_format(hh_date) + ".")
            latest_rs = sess.query(RateScript).filter(
                RateScript.contract == contract).order_by(
                RateScript.start_date.desc()).first()
            contract.update_rate_script(
                sess, latest_rs, latest_rs.start_date,
                latest_rs.start_date + relativedelta(months=2) - HH,
                loads(latest_rs.script))
            new_rs_start = latest_rs.start_date + relativedelta(months=1)
            contract.insert_rate_script(sess, new_rs_start, {})
            sess.commit()
            log_func(
                "Added a rate script starting at " + hh_format(new_rs_start) +
                ".")

            rs = sess.query(RateScript).filter(
                RateScript.contract == contract,
                RateScript.start_date <= hh_date, or_(
                    RateScript.finish_date == null(),
                    RateScript.finish_date >= hh_date)).first()

        rates = loads(rs.script)
        yr_cache[hh_date.month] = rs, rates

    try:
        rts = rates['tlms']
    except KeyError:
        rts = rates['tlms'] = {}

    key = key_format(hh_date)
    try:
        existing = rts[key]
    except KeyError:
        existing = rts[key] = {}

    try:
        group = existing[gsp_group_code]
    except KeyError:
        group = existing[gsp_group_code] = {}

    if run not in group:
        group[run] = {
            'off_taking': off_taking,
            'delivering': delivering}

        log_func(
            "Found rate at " + hh_format(hh_date) + " for GSP Group " +
            gsp_group_code + " and run " + run + ".")
    sess.rollback()


def get_importer():
    return tlm_importer


def startup():
    global tlm_importer
    if tlm_importer is not None:
        raise BadRequest("The TLM importer has already been started.")
    tlm_importer = TlmImporter()
    tlm_importer.start()


@atexit.register
def shutdown():
    if tlm_importer is not None:
        tlm_importer.stop()
