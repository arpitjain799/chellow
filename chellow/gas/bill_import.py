import collections
import datetime
import importlib
import threading
import traceback
from pkgutil import iter_modules

import pytz

from werkzeug.exceptions import BadRequest

import chellow.gas
from chellow.models import (
    BillType,
    GBatch,
    GReadType,
    GSupply,
    GUnit,
    Session,
)


importer_id = 0
import_lock = threading.Lock()
importers = {}

PARSER_PREFIX = "bill_parser_"


def find_parser_names():
    return ", ".join(
        "." + name[len(PARSER_PREFIX) :].replace("_", ".")
        for module_finder, name, ispkg in iter_modules(chellow.gas.__path__)
        if name.startswith(PARSER_PREFIX)
    )


class GBillImporter(threading.Thread):
    def __init__(self, sess, g_batch_id, file_name, file_bytes):
        threading.Thread.__init__(self)
        global importer_id
        self.importer_id = importer_id
        importer_id += 1

        self.g_batch_id = g_batch_id
        if len(file_bytes) == 0:
            raise BadRequest("File has zero length")
        imp_mod = None
        parts = file_name.split(".")[::-1]
        for i in range(len(parts)):
            nm = "bill_parser_" + "_".join(parts[: i + 1][::-1]).lower()
            try:
                imp_mod = nm, importlib.import_module(f"chellow.gas.{nm}")
            except ImportError:
                pass

        if imp_mod is None:
            raise BadRequest(
                f"Can't find a parser for the file '{file_name}'. The file name needs "
                f"to have an extension that's one of the following: "
                f"{find_parser_names()}."
            )

        self.parser_name = imp_mod[0]
        self.parser = imp_mod[1].Parser(file_bytes)
        self.successful_bills = []
        self.failed_bills = []
        self.log = collections.deque()
        self.bill_num = None

    def _log(self, msg):
        with import_lock:
            self.log.appendleft(
                datetime.datetime.now(pytz.utc).strftime("%Y-%m-%d %H:%M:%S")
                + " - "
                + msg
            )

    def status(self):
        return (
            f"Parsed file up to line number: {self.parser.line_number}. Inserting raw "
            f"bills up to bill: {self.bill_num}."
        )

    def run(self):
        sess = None
        try:
            self._log(f"Starting to parse the file with '{self.parser_name}'.")
            sess = Session()
            g_batch = GBatch.get_by_id(sess, self.g_batch_id)
            raw_bills = self.parser.make_raw_bills()
            self._log(
                "Successfully parsed the file, and now I'm starting to insert the raw "
                "bills."
            )
            for self.bill_num, raw_bill in enumerate(raw_bills):
                try:
                    bill_type = BillType.get_by_code(sess, raw_bill["bill_type_code"])
                    g_supply = GSupply.get_by_mprn(sess, raw_bill["mprn"])
                    g_bill = g_batch.insert_g_bill(
                        sess,
                        g_supply,
                        bill_type,
                        raw_bill["reference"],
                        raw_bill["account"],
                        raw_bill["issue_date"],
                        raw_bill["start_date"],
                        raw_bill["finish_date"],
                        raw_bill["kwh"],
                        raw_bill["net_gbp"],
                        raw_bill["vat_gbp"],
                        raw_bill["gross_gbp"],
                        raw_bill["raw_lines"],
                        raw_bill["breakdown"],
                    )
                    sess.flush()
                    for raw_read in raw_bill["reads"]:
                        prev_type = GReadType.get_by_code(
                            sess, raw_read["prev_type_code"]
                        )
                        pres_type = GReadType.get_by_code(
                            sess, raw_read["pres_type_code"]
                        )
                        g_unit = GUnit.get_by_code(sess, raw_read["unit"])
                        g_read = g_bill.insert_g_read(
                            sess,
                            raw_read["msn"],
                            g_unit,
                            raw_read["correction_factor"],
                            raw_read["calorific_value"],
                            raw_read["prev_value"],
                            raw_read["prev_date"],
                            prev_type,
                            raw_read["pres_value"],
                            raw_read["pres_date"],
                            pres_type,
                        )

                        sess.expunge(g_read)
                    self.successful_bills.append(raw_bill)
                    sess.expunge(g_bill)
                except BadRequest as e:
                    sess.rollback()
                    raw_bill["error"] = e.description
                    self.failed_bills.append(raw_bill)

            if len(self.failed_bills) == 0:
                sess.commit()
                self._log(
                    "All the bills have been successfully loaded and attached to the "
                    "batch."
                )
            else:
                sess.rollback()
                self._log(
                    f"The import has finished, but {len(self.failed_bills)} bills "
                    f"failed to load, and so the whole import has been rolled back."
                )

        except BadRequest as e:
            self._log(e.description)
        except BaseException:
            self._log(f"I've encountered a problem: {traceback.format_exc()}")
        finally:
            if sess is not None:
                sess.rollback()
                sess.close()

    def make_fields(self):
        with import_lock:
            fields = {
                "log": tuple(self.log),
                "is_alive": self.is_alive(),
                "importer_id": self.importer_id,
            }
            if not self.is_alive():
                fields["successful_bills"] = self.successful_bills
                fields["failed_bills"] = self.failed_bills
            return fields


def start_bill_importer(sess, batch_id, file_name, file_bytes):
    with import_lock:
        bi = GBillImporter(sess, batch_id, file_name, file_bytes)
        importers[bi.importer_id] = bi
        bi.start()

    return bi.importer_id


def get_bill_importer_ids(g_batch_id):
    with import_lock:
        return [k for k, v in importers.items() if v.g_batch_id == g_batch_id]


def get_bill_importer(id):
    with import_lock:
        return importers[id]
