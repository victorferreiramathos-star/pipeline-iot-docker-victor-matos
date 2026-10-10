"""Testes reais no PostgreSQL local; alterações de teste sempre sofrem rollback."""

from hashlib import sha256
import unittest

import pandas as pd
from sqlalchemy import text

from src.ingest import (CSV, OFFICIAL_HASH, database_engine, ingest,
                        load_frame, validate)


class IngestionTests(unittest.TestCase):
    def test_01_official_load_twice_and_reconciliation(self):
        first = ingest()
        second = ingest()
        self.assertEqual(first['source_rows'], 97606)
        self.assertEqual(first['duplicate_rows'], 1)
        self.assertEqual(first['rejected_rows'], 0)
        self.assertEqual(first['inserted_rows'] + first['existing_rows'], 97605)
        self.assertEqual(second['inserted_rows'], 0)
        self.assertEqual(second['existing_rows'], 97605)
        engine = database_engine()
        try:
            with engine.connect() as conn:
                self.assertEqual(conn.scalar(text('SELECT count(*) FROM iot.temperature_readings')), 97605)
                for result in (first, second):
                    audit = conn.execute(text('SELECT * FROM audit.ingestion_runs WHERE run_id=:id'),
                                         {'id': result['run_id']}).mappings().one()
                    self.assertEqual(audit['status'], 'completed')
                    self.assertEqual(audit['sha256'], OFFICIAL_HASH)
                    self.assertEqual(audit['source_rows'], sum(audit[k] for k in
                                     ['duplicate_rows', 'rejected_rows', 'inserted_rows', 'existing_rows']))
                    # Compara todos os campos brutos, inclusive a duplicata original.
                    raw = conn.execute(text('''SELECT id, "room_id/id", noted_date, temp, "out/in"
                        FROM staging.temperature_raw WHERE run_id=:id ORDER BY source_row'''),
                        {'id': result['run_id']}).all()
                    frame = pd.read_csv(CSV, dtype=str, keep_default_na=False)
                    self.assertEqual([tuple(r) for r in raw], list(frame.itertuples(index=False, name=None)))
                persisted = conn.execute(text('''SELECT source_id, location_name, observed_at,
                    temperature, environment FROM iot.temperature_readings''')).all()
                expected = {(r['id'], *validate(r)) for r in frame.to_dict('records')}
                self.assertEqual(set(tuple(r) for r in persisted), expected)
        finally:
            engine.dispose()
        print('CARGA_1', first)
        print('CARGA_2', second)

    def test_02_invalid_row_conflict_and_rollback(self):
        original_hash = sha256(CSV.read_bytes()).hexdigest()
        frame = pd.read_csv(CSV, dtype=str, keep_default_na=False).head(2).copy()
        frame.iloc[0, frame.columns.get_loc('noted_date')] = '31-02-2018 09:30'
        frame.iloc[1, frame.columns.get_loc('temp')] = '100'
        engine = database_engine()
        try:
            with engine.connect() as conn:
                before = conn.scalar(text('SELECT count(*) FROM audit.ingestion_runs'))
                conn.rollback()
                transaction = conn.begin()
                try:
                    result = load_frame(conn, frame, original_hash, 'TEST_ONLY_ROLLBACK')
                    self.assertEqual(result['rejected_rows'], 2)
                    reasons = set(conn.execute(text('''SELECT reason FROM audit.ingestion_rejections
                        WHERE run_id=:id'''), {'id': result['run_id']}).scalars())
                    self.assertEqual(reasons, {'invalid_date', 'conflicting_source_id_in_database'})
                    self.assertEqual(result['inserted_rows'], 0)
                finally:
                    transaction.rollback()
                self.assertEqual(conn.scalar(text('SELECT count(*) FROM audit.ingestion_runs')), before)
                self.assertEqual(conn.scalar(text('SELECT count(*) FROM iot.temperature_readings')), 97605)
        finally:
            engine.dispose()
        self.assertEqual(sha256(CSV.read_bytes()).hexdigest(), original_hash)

    def test_03_validation_and_in_file_conflict(self):
        row = pd.read_csv(CSV, dtype=str, keep_default_na=False).iloc[0].to_dict()
        for column, bad in [('temp', '29.5'), ('out/in', 'Unknown'), ('noted_date', '2018-12-08 09:30')]:
            with self.subTest(column=column), self.assertRaises(ValueError):
                validate(dict(row, **{column: bad}))
        other = dict(row, temp='30')
        engine = database_engine()
        try:
            with engine.connect() as conn:
                tx = conn.begin()
                try:
                    result = load_frame(conn, pd.DataFrame([row, other]), OFFICIAL_HASH, 'TEST_ONLY_ROLLBACK')
                    self.assertEqual(result['rejected_rows'], 2)
                    self.assertEqual(result['inserted_rows'], 0)
                finally:
                    tx.rollback()
        finally:
            engine.dispose()


if __name__ == '__main__':
    unittest.main(verbosity=2)
