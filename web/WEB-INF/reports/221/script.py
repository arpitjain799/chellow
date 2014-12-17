from net.sf.chellow.monad import Monad
import db
import system_price_bmreports
import templater
import utils
Monad.getUtils()['impt'](
    globals(), 'db', 'utils', 'templater', 'system_price_bmreports')
Contract = db.Contract
inv, template = globals()['inv'], globals()['template']


sess = None
importer = None
try:
    sess = db.session()
    if inv.getRequest().getMethod() == "GET":
        importer = system_price_bmreports.get_importer()
        contract = Contract.get_non_core_by_name(
            sess, 'system_price_bmreports')
        templater.render(
            inv, template, {'importer': importer, 'contract': contract})
    else:
        importer = system_price_bmreports.get_importer()
        contract = Contract.get_non_core_by_name(
            sess, 'system_price_bmreports')
        importer.go()
        inv.sendSeeOther("/reports/221/output/")
except utils.UserException, e:
    sess.rollback()
    templater.render(
        inv, template, {
            'messages': [str(e)], 'importer': importer, 'contract': contract})
finally:
    if sess is not None:
        sess.close()
