from sqlalchemy import or_
from sqlalchemy.sql.expression import null, true
from net.sf.chellow.monad import Monad
from datetime import datetime
import pytz
import utils
import db

Monad.getUtils()['impt'](globals(), 'db', 'utils', 'templater', 'bsuos')
prev_hh, hh_after, hh_before = utils.prev_hh, utils.hh_after, utils.hh_before
Supply, Source, Era, Site = db.Supply, db.Source, db.Era, db.Site
SiteEra = db.SiteEra
inv = globals()['inv']

year = inv.getInteger('year')
if inv.hasParameter('supply_id'):
    supply_id = inv.getLong('supply_id')
else:
    supply_id = None


def content():
    yield "MPAN Core,Site Id,Site Name,Date,Event,"

    year_start = datetime(year, 4, 1, tzinfo=pytz.utc)
    year_finish = prev_hh(datetime(year + 1, 4, 1, tzinfo=pytz.utc))

    def add_event(events, date, code, era=None, mpan_core=None):
        if era is None:
            mpan_cores = [mpan_core]
        else:
            mpan_cores = []
            if era.imp_mpan_core is not None:
                mpan_cores.append(era.imp_mpan_core)
            if era.exp_mpan_core is not None:
                mpan_cores.append(era.exp_mpan_core)

        for mpan_core in mpan_cores:
            events.append({'date': date, 'code': code, 'mpan-core': mpan_core})

    sess = None
    try:
        sess = db.session()
        if supply_id is None:
            supplies = sess.query(Supply).join(Source).join(Era).filter(
                Source.code.in_(('net', 'gen-net', 'gen')),
                Era.start_date <= year_finish, or_(
                    Era.finish_date == null(),
                    Era.finish_date >= year_start)).distinct()
        else:
            supply = Supply.get_by_id(supply_id)
            supplies = sess.query(Supply).filter(Supply.id == supply.id)

        for supply in supplies:
            eras = sess.query(Era).filter(
                Era.supply == supply, Era.start_date <= year_finish,
                or_(Era.finish_date == null(), Era.finish_date >= year_start)
                ).order_by(Era.start_date).all()
            events = []
            first_era = eras[0]
            first_era_start = first_era.start_date
            if hh_after(first_era_start, year_start):
                add_event(events, first_era_start, "New Supply", first_era)

            last_era = eras[-1]
            last_era_finish = last_era.finish_date
            if hh_before(last_era_finish, year_finish):
                add_event(events, last_era_finish, "Disconnection", last_era)

            prev_era = first_era
            for era in eras[1:]:
                if era.msn != prev_era.msn:
                    add_event(events, era.start_date, "Meter Change", era)
                if era.pc.code != prev_era.pc.code:
                    add_event(
                        events, era.start_date, "Change Of Profile Class", era)

                if era.mop_contract_id != prev_era.mop_contract_id:
                    add_event(events, era.start_date, "Change Of MOP", era)

                if era.hhdc_contract_id != prev_era.hhdc_contract_id:
                    add_event(events, era.start_date, "Change Of DC", era)

                for is_import in [True, False]:
                    if era.imp_mpan_core is None:
                        mpan_core = era.exp_mpan_core
                    else:
                        mpan_core = era.imp_mpan_core

                    if is_import:
                        cur_sup = era.imp_supplier_contract
                        prev_sup = prev_era.imp_supplier_contract
                    else:
                        cur_sup = era.exp_supplier_contract
                        prev_sup = prev_era.exp_supplier_contract

                    if cur_sup is None and prev_sup is not None:
                        add_event(
                            events, era.start_date, "End of supply", mpan_core)
                    elif cur_sup is not None and prev_sup is None:
                        add_event(
                            events, era.start_date, "Start of supply", None,
                            mpan_core)
                    elif cur_sup is not None and \
                            prev_sup is not None and cur_sup != prev_sup:
                        add_event(
                            events, era.start_date, "Change Of Supplier", None,
                            mpan_core)

                prev_era = era

            if len(events) > 0:
                site = sess.query(Site).join(SiteEra).filter(
                    SiteEra.is_physical == true(),
                    SiteEra.era == last_era).one()

                for event in events:
                    vals = [
                        event['mpan-core'], site.code, site.name,
                        event['date'].strftime("%Y-%m-%d %H:%M"),
                        event['code']]
                    yield '\n,'.join(
                        '"' + str(val) + '"' for val in vals) + ','
            else:
                yield ' '
    finally:
        sess.close()

utils.send_response(
    inv, content, status=200, mimetype='text/csv',
    file_name='output.csv')
