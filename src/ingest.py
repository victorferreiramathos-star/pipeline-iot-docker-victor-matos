"""Ingestão transacional do CSV oficial: python -m src.ingest."""

from datetime import datetime
from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path
import re
from uuid import uuid4

import pandas as pd
from psycopg2.extras import execute_values
from sqlalchemy import URL, create_engine, text

ROOT = Path(__file__).resolve().parents[1]
CSV = ROOT / 'data' / 'IOT-temp.csv'
OFFICIAL_HASH = '2bf965701db96cd5788403d395a25d2dd7282bea24e317b7f7b157b7a02063d4'
COLUMNS = ['id', 'room_id/id', 'noted_date', 'temp', 'out/in']


def database_engine():
    """Credenciais exclusivamente do .env local, sem URL sensível em logs."""
    config = {}
    for line in (ROOT / '.env').read_text(encoding='utf-8').splitlines():
        if line.strip() and not line.lstrip().startswith('#'):
            key, value = line.split('=', 1)
            config[key.strip()] = value.strip()
    url = URL.create('postgresql+psycopg2', username=config['POSTGRES_USER'],
                     password=config['POSTGRES_PASSWORD'], host=config['POSTGRES_HOST'],
                     port=int(config['POSTGRES_PORT']), database=config['POSTGRES_DB'])
    return create_engine(url, hide_parameters=True, connect_args={'connect_timeout': 10})


def prepare_database(conn):
    for schema in ('audit', 'staging', 'iot'):
        conn.execute(text(f'CREATE SCHEMA IF NOT EXISTS {schema}'))
    conn.execute(text('''
        CREATE TABLE IF NOT EXISTS audit.ingestion_runs (
          run_id UUID PRIMARY KEY, source_file TEXT NOT NULL, sha256 TEXT NOT NULL,
          started_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
          finished_at TIMESTAMPTZ, status TEXT NOT NULL,
          source_rows INTEGER NOT NULL, duplicate_rows INTEGER NOT NULL DEFAULT 0,
          rejected_rows INTEGER NOT NULL DEFAULT 0, inserted_rows INTEGER NOT NULL DEFAULT 0,
          existing_rows INTEGER NOT NULL DEFAULT 0,
          CHECK (status <> 'completed' OR source_rows =
            duplicate_rows + rejected_rows + inserted_rows + existing_rows));
        CREATE TABLE IF NOT EXISTS staging.temperature_raw (
          run_id UUID REFERENCES audit.ingestion_runs(run_id), source_row INTEGER NOT NULL,
          id TEXT, "room_id/id" TEXT, noted_date TEXT, temp TEXT, "out/in" TEXT,
          PRIMARY KEY (run_id, source_row));
        CREATE TABLE IF NOT EXISTS audit.ingestion_rejections (
          run_id UUID NOT NULL, source_row INTEGER NOT NULL, reason TEXT NOT NULL,
          PRIMARY KEY (run_id, source_row),
          FOREIGN KEY (run_id, source_row) REFERENCES staging.temperature_raw);
        CREATE TABLE IF NOT EXISTS iot.temperature_readings (
          source_id TEXT PRIMARY KEY, location_name TEXT NOT NULL,
          observed_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, temperature SMALLINT NOT NULL,
          environment TEXT NOT NULL CHECK (environment IN ('In', 'Out')),
          run_id UUID NOT NULL REFERENCES audit.ingestion_runs(run_id));
    '''))


def validate(row):
    """Sem inferência de datas ou correção silenciosa de valores."""
    if any(not isinstance(row.get(c), str) or not row[c].strip() for c in COLUMNS):
        raise ValueError('missing_value')
    if not re.fullmatch(r'\d{2}-\d{2}-\d{4} \d{2}:\d{2}', row['noted_date']):
        raise ValueError('invalid_date')
    try:
        date = datetime.strptime(row['noted_date'], '%d-%m-%Y %H:%M')
    except ValueError:
        raise ValueError('invalid_date') from None
    if not re.fullmatch(r'[+-]?\d+', row['temp']):
        raise ValueError('invalid_integer_temperature')
    temperature = int(row['temp'])
    if not -32768 <= temperature <= 32767:
        raise ValueError('temperature_out_of_storage_range')
    if row['out/in'] not in ('In', 'Out'):
        raise ValueError('invalid_environment')
    return (row['room_id/id'], date, temperature, row['out/in'])


def load_frame(conn, frame, digest, source_file):
    """Executa na transação do chamador; testes podem reverter todas as alterações."""
    if list(frame.columns) != COLUMNS:
        raise ValueError('unexpected_columns')
    conn.execute(text('SELECT pg_advisory_xact_lock(8675309)'))
    run_id = str(uuid4())
    counts = dict(source_rows=len(frame), duplicate_rows=0, rejected_rows=0,
                  inserted_rows=0, existing_rows=0)
    conn.execute(text('''INSERT INTO audit.ingestion_runs
        (run_id, source_file, sha256, status, source_rows)
        VALUES (:run_id, :file, :hash, 'running', :rows)'''),
        dict(run_id=run_id, file=source_file, hash=digest, rows=len(frame)))
    raw = frame.copy()
    raw.insert(0, 'source_row', range(2, len(frame) + 2))
    raw.insert(0, 'run_id', run_id)
    # SQLAlchemy controla a transação; psycopg2 envia lotes sem commit próprio.
    with conn.connection.driver_connection.cursor() as cursor:
        execute_values(cursor, '''INSERT INTO staging.temperature_raw
            (run_id, source_row, id, "room_id/id", noted_date, temp, "out/in") VALUES %s''',
            list(raw.itertuples(index=False, name=None)), page_size=2000)
    existing = {r[0]: tuple(r[1:]) for r in conn.execute(text('''
        SELECT source_id, location_name, observed_at, temperature, environment
        FROM iot.temperature_readings'''))}
    records = frame.to_dict('records')
    variants = {}
    for row in records:
        variants.setdefault(row['id'], set()).add(tuple(row[c] for c in COLUMNS))
    seen, pending, rejections = set(), [], []
    for number, row in enumerate(records, start=2):
        original = tuple(row[c] for c in COLUMNS)
        if original in seen:
            counts['duplicate_rows'] += 1
            continue
        seen.add(original)
        reason = None
        try:
            value = validate(row)
            if len(variants[row['id']]) > 1:
                reason = 'conflicting_source_id_in_file'
            elif row['id'] in existing:
                if existing[row['id']] == value:
                    counts['existing_rows'] += 1
                    continue
                reason = 'conflicting_source_id_in_database'
        except ValueError as exc:
            reason = str(exc)
        if reason:
            rejections.append(dict(run_id=run_id, source_row=number, reason=reason))
            counts['rejected_rows'] += 1
        else:
            pending.append(dict(source_id=row['id'], location_name=value[0],
                                observed_at=value[1], temperature=value[2],
                                environment=value[3], run_id=run_id))
    if pending:
        with conn.connection.driver_connection.cursor() as cursor:
            execute_values(cursor, '''INSERT INTO iot.temperature_readings
                (source_id, location_name, observed_at, temperature, environment, run_id)
                VALUES %s''', [tuple(row[k] for k in ('source_id', 'location_name',
                    'observed_at', 'temperature', 'environment', 'run_id')) for row in pending],
                page_size=2000)
    if rejections:
        conn.execute(text('''INSERT INTO audit.ingestion_rejections
            (run_id, source_row, reason) VALUES (:run_id, :source_row, :reason)'''), rejections)
    counts['inserted_rows'] = len(pending)
    if counts['source_rows'] != sum(counts[k] for k in counts if k != 'source_rows'):
        raise RuntimeError('reconciliation_failed')
    conn.execute(text('''UPDATE audit.ingestion_runs SET status='completed',
        finished_at=clock_timestamp(), duplicate_rows=:duplicate_rows,
        rejected_rows=:rejected_rows, inserted_rows=:inserted_rows,
        existing_rows=:existing_rows WHERE run_id=:run_id'''), dict(run_id=run_id, **counts))
    return dict(run_id=run_id, **counts)


def ingest():
    content = CSV.read_bytes()
    digest = sha256(content).hexdigest()
    if digest != OFFICIAL_HASH:
        raise ValueError('official_csv_hash_mismatch')
    frame = pd.read_csv(BytesIO(content), dtype=str, keep_default_na=False)
    engine = database_engine()
    try:
        with engine.begin() as conn:
            prepare_database(conn)
            result = load_frame(conn, frame, digest, CSV.name)
        return result
    finally:
        engine.dispose()


if __name__ == '__main__':
    try:
        print(json.dumps(ingest()))
    except Exception:
        print('Falha na ingestão; transação revertida. Verifique acesso, dependências e arquivo local.')
        raise SystemExit(1) from None
