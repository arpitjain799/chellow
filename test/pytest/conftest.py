
import chellow.models
from chellow import create_app
from chellow.models import (
    Session, stop_sqlalchemy
)

from flask.testing import FlaskClient

import pg8000

import pytest

from requests.auth import _basic_auth_str


def fresh_db():
    stop_sqlalchemy()
    config = chellow.models.config
    database = config['PGDATABASE']
    with pg8000.connect(
            config['PGUSER'], host=config['PGHOST'], database='postgres',
            port=int(config['PGPORT']), password=config['PGPASSWORD']) as con:
        cursor = con.cursor()
        con.rollback()
        con.autocommit = True
        cursor.execute(f"DROP DATABASE IF EXISTS {database};")
        cursor.execute(f"CREATE DATABASE {database} ENCODING 'UTF8';")


@pytest.fixture
def app():
    fresh_db()
    return create_app(testing=True)


@pytest.fixture
def raw_client(app):
    return app.test_client()


class CustomClient(FlaskClient):
    def open(self, *args, **kwargs):
        if 'headers' in kwargs:
            headers = kwargs['headers']
        else:
            headers = kwargs['headers'] = {}

        headers['Authorization'] = _basic_auth_str(
            'admin@example.com', 'admin')
        return super().open(*args, **kwargs)


@pytest.fixture
def sess(app):
    sess = Session()
    yield sess
    sess.close()


@pytest.fixture
def client(app, sess):
    sess.execute("INSERT INTO user_role (code) VALUES ('editor')")

    sess.execute(
        "INSERT INTO market_role (code, description) "
        "VALUES ('Z', 'Non-core Role')")
    sess.execute(
        "INSERT INTO participant (code, name) "
        "VALUES ('NEUT', 'Neutral')")
    sess.execute(
        "INSERT INTO party (market_role_id, participant_id, name, "
        "valid_from, valid_to, dno_code) "
        "VALUES (1, 1, 'Neutral Party', '2000-01-01', null, null)")
    sess.execute(
        "INSERT INTO contract (name, charge_script, properties, "
        "state, market_role_id, party_id, start_rate_script_id, "
        "finish_rate_script_id) VALUES ('configuration', '{}', '{}', "
        "'{}', 1, 1, null, null)")
    sess.execute(
        "INSERT INTO rate_script (contract_id, start_date, finish_date, "
        "script) VALUES (1, '2020-01-01', '2020-01-31', '{}')")
    sess.execute(
        "UPDATE contract set start_rate_script_id = 1, "
        "finish_rate_script_id = 1 where id = 1;")
    sess.commit()

    app.test_client_class = CustomClient

    return app.test_client()


@pytest.fixture
def runner(app):
    return app.test_cli_runner()
