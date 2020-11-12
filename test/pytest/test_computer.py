import chellow.computer
from chellow.models import (
    Contract, Cop, GspGroup, MarketRole, MeterPaymentType, MeterType, Mtc,
    Participant, Pc, Site, Source, VoltageLevel, insert_cops, insert_sources,
    insert_voltage_levels
)
from chellow.utils import utc_datetime


def test_find_pair(mocker):
    sess = mocker.Mock()
    caches = {}
    is_forwards = True
    first_read = {
        'date': utc_datetime(2010, 1, 1),
        'reads': {},
        'msn': 'kh'
    }
    second_read = {
        'date': utc_datetime(2010, 2, 1),
        'reads': {},
        'msn': 'kh'
    }
    read_list = [first_read, second_read]
    pair = chellow.computer._find_pair(sess, caches, is_forwards, read_list)
    assert pair['start-date'] == utc_datetime(2010, 1, 1)


def test_find_hhs_empty_pairs(mocker):
    mocker.patch("chellow.computer.is_tpr", return_value=True)
    caches = {}
    sess = mocker.Mock()
    pairs = []
    chunk_start = utc_datetime(2010, 1, 1)
    chunk_finish = utc_datetime(2010, 1, 1)
    hhs = chellow.computer._find_hhs(
        caches, sess, pairs, chunk_start, chunk_finish)
    assert hhs == {
        utc_datetime(2010, 1, 1): {
            'msp-kw': 0, 'msp-kwh': 0, 'hist-kwh': 0, 'imp-msp-kvar': 0,
            'imp-msp-kvarh': 0, 'exp-msp-kvar': 0, 'exp-msp-kvarh': 0,
            'tpr': '00001'
        }
    }


def test_find_hhs_two_pairs(mocker):
    mocker.patch("chellow.computer.is_tpr", return_value=True)
    caches = {}
    sess = mocker.Mock()
    pairs = [
        {
            'start-date': utc_datetime(2010, 1, 1),
            'tprs': {
                '00001': 1
            }
        },
        {
            'start-date': utc_datetime(2010, 1, 1, 0, 30),
            'tprs': {
                '00001': 1
            }
        }
    ]
    chunk_start = utc_datetime(2010, 1, 1)
    chunk_finish = utc_datetime(2010, 1, 1, 0, 30)
    hhs = chellow.computer._find_hhs(
        caches, sess, pairs, chunk_start, chunk_finish)
    assert hhs == {
        utc_datetime(2010, 1, 1): {
            'msp-kw': 2.0, 'msp-kwh': 1.0, 'hist-kwh': 1.0, 'imp-msp-kvar': 0,
            'imp-msp-kvarh': 0, 'exp-msp-kvar': 0, 'exp-msp-kvarh': 0,
            'tpr': '00001'
        },
        utc_datetime(2010, 1, 1, 0, 30): {
            'msp-kw': 2.0, 'msp-kwh': 1.0, 'hist-kwh': 1.0, 'imp-msp-kvar': 0,
            'imp-msp-kvarh': 0, 'exp-msp-kvar': 0, 'exp-msp-kvarh': 0,
            'tpr': '00001'
        }
    }


def test_set_status(mocker):
    hhs = {
        utc_datetime(2012, 2, 1): {}
    }

    read_list = [
        {
            'date': utc_datetime(2012, 1, 1)
        }
    ]
    forecast_date = utc_datetime(2012, 3, 1)
    chellow.computer._set_status(hhs, read_list, forecast_date)
    assert hhs == {
        utc_datetime(2012, 2, 1): {
            'status': 'A'
        }
    }


def test_make_reads_forwards(mocker):
    is_forwards = True
    msn = 'k'
    read_a = {'date': utc_datetime(2018, 3, 10), 'msn': msn}
    read_b = {'date': utc_datetime(2018, 3, 13), 'msn': msn}
    prev_reads = iter([read_a])
    pres_reads = iter([read_b])
    actual = list(
        chellow.computer._make_reads(is_forwards, prev_reads, pres_reads))
    expected = [read_a, read_b]
    assert actual == expected


def test_make_reads_forwards_meter_change(mocker):
    is_forwards = True
    dt = utc_datetime(2018, 3, 1)
    read_a = {'date': dt, 'msn': 'a'}
    read_b = {'date': dt, 'msn': 'b'}
    prev_reads = iter([read_a])
    pres_reads = iter([read_b])
    actual = list(
        chellow.computer._make_reads(is_forwards, prev_reads, pres_reads))
    expected = [read_b, read_a]
    assert actual == expected


def test_make_reads_backwards(mocker):
    is_forwards = False
    msn = 'k'
    read_a = {'date': utc_datetime(2018, 3, 10), 'msn': msn}
    read_b = {'date': utc_datetime(2018, 3, 13), 'msn': msn}
    prev_reads = iter([read_a])
    pres_reads = iter([read_b])
    actual = list(
        chellow.computer._make_reads(is_forwards, prev_reads, pres_reads))
    expected = [read_b, read_a]
    assert actual == expected


def test_init_hh_data(sess, mocker):
    """New style channels
    """
    site = Site.insert(sess, 'CI017', 'Water Works')
    market_role_Z = MarketRole.insert(sess, 'Z', 'Non-core')
    participant = Participant.insert(sess, 'CALB', 'AK Industries')
    participant.insert_party(
        sess, market_role_Z, 'None core', utc_datetime(2000, 1, 1), None, None)
    bank_holiday_rate_script = {
        'bank_holidays': []
    }
    Contract.insert_non_core(
        sess, 'bank_holidays', '', {}, utc_datetime(2000, 1, 1), None,
        bank_holiday_rate_script)
    market_role_X = MarketRole.insert(sess, 'X', 'Supplier')
    market_role_M = MarketRole.insert(sess, 'M', 'Mop')
    market_role_C = MarketRole.insert(sess, 'C', 'HH Dc')
    market_role_R = MarketRole.insert(sess, 'R', 'Distributor')
    participant.insert_party(
        sess, market_role_M, 'Fusion Mop Ltd', utc_datetime(2000, 1, 1), None,
        None)
    participant.insert_party(
        sess, market_role_X, 'Fusion Ltc', utc_datetime(2000, 1, 1), None,
        None)
    participant.insert_party(
        sess, market_role_C, 'Fusion DC', utc_datetime(2000, 1, 1), None, None)
    mop_contract = Contract.insert_mop(
        sess, 'Fusion', participant, '', {}, utc_datetime(2000, 1, 1), None,
        {})
    dc_contract = Contract.insert_hhdc(
        sess, 'Fusion DC 2000', participant, '', {}, utc_datetime(2000, 1, 1),
        None, {})
    pc = Pc.insert(sess, '00', 'hh', utc_datetime(2000, 1, 1), None)
    insert_cops(sess)
    cop = Cop.get_by_code(sess, '5')
    imp_supplier_contract = Contract.insert_supplier(
        sess, 'Fusion Supplier 2000', participant, '', {},
        utc_datetime(2000, 1, 1), None, {})
    dno = participant.insert_party(
        sess, market_role_R, 'WPD', utc_datetime(2000, 1, 1), None, '22')
    meter_type = MeterType.insert(
        sess, 'C5', 'COP 1-5', utc_datetime(2000, 1, 1), None)
    meter_payment_type = MeterPaymentType.insert(
        sess, 'CR', 'Credit', utc_datetime(1996, 1, 1), None)
    Mtc.insert(
        sess, None, '845', 'HH COP5 And Above With Comms', False, False, True,
        meter_type, meter_payment_type, 0, utc_datetime(1996, 1, 1), None)
    insert_voltage_levels(sess)
    voltage_level = VoltageLevel.get_by_code(sess, 'HV')
    dno.insert_llfc(
        sess, '510', 'PC 5-8 & HH HV', voltage_level, False, True,
        utc_datetime(1996, 1, 1), None)
    dno.insert_llfc(
        sess, '521', 'Export (HV)', voltage_level, False, False,
        utc_datetime(1996, 1, 1), None)
    insert_sources(sess)
    source = Source.get_by_code(sess, 'net')
    gsp_group = GspGroup.insert(sess, '_L', 'South Western')
    supply = site.insert_e_supply(
        sess, source, None, "Bob", utc_datetime(2000, 1, 1),
        None, gsp_group, mop_contract, '773', dc_contract, 'ghyy3', 'hgjeyhuw',
        pc, '845', cop, None, {}, '22 7867 6232 781', '510',
        imp_supplier_contract, '7748', 361, None, None, None, None, None)
    era = supply.eras[0]
    channel = era.insert_channel(sess, True, 'ACTIVE')
    data_raw = [
        {
            'start_date': utc_datetime(2009, 8, 10),
            'value': 10,
            'status': 'A',
        }
    ]
    channel.add_hh_data(sess, data_raw)

    sess.commit()

    caches = {}
    chunk_start = utc_datetime(2009, 7, 31, 23, 00)
    chunk_finish = utc_datetime(2009, 8, 31, 22, 30)
    is_import = True
    full_channels, hhd = chellow.computer._init_hh_data(
        sess, caches, era, chunk_start, chunk_finish, is_import)

    assert full_channels

    expected_hhd = {
        utc_datetime(2009, 8, 10): {
            'imp-msp-kvarh': 0.0,
            'imp-msp-kvar': 0.0,
            'exp-msp-kvarh': 0.0,
            'exp-msp-kvar': 0.0,
            'status': 'A',
            'hist-kwh': 10.0,
            'msp-kwh': 10.0,
            'msp-kw': 20.0
        }
    }
    assert hhd == expected_hhd
