from chellow.e.bill_parsers.settlement_dc_stark_xlsx import Parser


def test(sess):
    f = open(
        "test/e/bill_parsers/test_bill_parser_settlement_dc_stark_xlsx/"
        "bills.settlement.dc.stark.xlsx",
        mode="rb",
    )
    parser = Parser(f)
    parser.make_raw_bills()
