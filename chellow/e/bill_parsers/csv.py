import csv
from decimal import Decimal, InvalidOperation
from io import StringIO

from dateutil.relativedelta import relativedelta

from werkzeug.exceptions import BadRequest

from chellow.utils import (
    HH,
    ct_datetime_parse,
    loads,
    parse_mpan_core,
    to_utc,
    validate_hh_start,
)


def parse_date(row, idx, is_finish=False):
    date_str = row[idx].strip()
    try:
        if len(date_str) == 10:
            dt = to_utc(ct_datetime_parse(date_str, "%Y-%m-%d"))
            if is_finish:
                dt = dt + relativedelta(days=1) - HH
        else:
            dt = to_utc(ct_datetime_parse(date_str, "%Y-%m-%d %H:%M"))
        return validate_hh_start(dt)
    except ValueError as e:
        raise BadRequest(
            f"Difficulty parsing a date in the row {row} at position " f"{idx}: {e}"
        )


class Parser:
    def __init__(self, f):
        self.reader = csv.reader(
            StringIO(str(f.read(), "utf-8", errors="ignore")), skipinitialspace=True
        )
        self.line_number = None

    def make_raw_bills(self):
        raw_bills = []
        next(iter(self.reader))  # skip title row
        blank_set = set(("",))
        for self.line_number, self.vals in enumerate(self.reader):
            # skip blank lines
            if len(self.vals) == 0 or set(self.vals) == blank_set:
                continue

            bill_type_code = self.vals[0]
            if bill_type_code.startswith("#"):
                continue  # skip comment lines
            account = self.vals[1]
            mpan_core = parse_mpan_core(self.vals[2])
            reference = self.vals[3]
            issue_date = parse_date(self.vals, 4)
            start_date = parse_date(self.vals, 5)
            finish_date = parse_date(self.vals, 6, True)

            kwh = self.to_decimal(7, "kwh")
            net = self.to_decimal(8, "net", True)
            vat = self.to_decimal(9, "vat", True)
            gross = self.to_decimal(10, "gross", True)

            if len(self.vals) > 11:
                breakdown_str = self.vals[11].strip()
                if len(breakdown_str) == 0:
                    breakdown = {}
                else:
                    try:
                        breakdown = loads(breakdown_str)
                    except SyntaxError as e:
                        raise BadRequest(str(e))
            else:
                raise BadRequest(
                    f"For the line, {self.vals} there isn't a 'breakdown' "
                    f"field on the end."
                )

            while self.vals[-1] == "" and len(self.vals) > 12:
                del self.vals[-1]

            reads = []
            for i in range(12, len(self.vals), 11):
                tpr_str = self.vals[i + 4].strip()
                tpr_code = None if len(tpr_str) == 0 else tpr_str.zfill(5)
                reads.append(
                    {
                        "msn": self.vals[i],
                        "mpan": self.vals[i + 1],
                        "coefficient": self.to_decimal(i + 2, "coefficient"),
                        "units": self.vals[i + 3],
                        "tpr_code": tpr_code,
                        "prev_date": parse_date(self.vals, i + 5),
                        "prev_value": Decimal(self.vals[i + 6]),
                        "prev_type_code": self.vals[i + 7],
                        "pres_date": parse_date(self.vals, i + 8),
                        "pres_value": Decimal(self.vals[i + 9]),
                        "pres_type_code": self.vals[i + 10],
                    }
                )

            raw_bill = {
                "bill_type_code": bill_type_code,
                "account": account,
                "mpan_core": mpan_core,
                "reference": reference,
                "issue_date": issue_date,
                "start_date": start_date,
                "finish_date": finish_date,
                "kwh": kwh,
                "net": net,
                "vat": vat,
                "gross": gross,
                "breakdown": breakdown,
                "reads": reads,
            }
            raw_bills.append(raw_bill)

        return raw_bills

    def to_decimal(self, dec_index, dec_name, is_money=False):
        try:
            dec_str = self.vals[dec_index]
            dec = Decimal(dec_str)
            if is_money:
                dec += Decimal("0.00")
            return dec
        except InvalidOperation as e:
            raise BadRequest(
                f"The value '{dec_str}' can't be parsed as a decimal: {e}. It's in "
                f"the '{dec_name}' column at position {dec_index} in {self.vals}."
            )
        except IndexError:
            raise BadRequest(
                f"The field '{dec_name}' can't be found. It's expected at "
                f"position {dec_index} in the list of fields."
            )
        except ValueError:
            raise BadRequest(
                f"The {dec_name} field '{dec_str}' cannot be parsed as a "
                f"number. The {dec_name} field is the {dec_index} field of "
                f"{self.vals}."
            )
