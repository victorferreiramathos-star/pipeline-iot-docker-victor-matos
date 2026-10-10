"""Oracle Python independente das agregações SQL; consultas somente de leitura."""

from collections import defaultdict
from decimal import Decimal
from datetime import datetime, time
from hashlib import sha256
import json
import unittest

from sqlalchemy import text

from src.ingest import CSV, OFFICIAL_HASH, database_engine


class ViewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = database_engine()
        cls.conn = cls.engine.connect()
        cls.conn.execute(text('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY'))
        cls.source = cls.conn.execute(text('''SELECT source_id, location_name,
            observed_at, temperature, environment FROM iot.temperature_readings''')).all()
        cls.daily, cls.hourly = defaultdict(list), defaultdict(list)
        for _, local, date, temp, env in cls.source:
            cls.daily[(date.date(), local, env)].append(temp)
            cls.hourly[(date.replace(minute=0, second=0, microsecond=0), local, env)].append((date, temp))

    @classmethod
    def tearDownClass(cls):
        cls.conn.close()
        cls.engine.dispose()

    def rows(self, name, order):
        rows = self.conn.execute(text(f'SELECT * FROM iot.{name} ORDER BY {order}')).mappings().all()
        print(name, 'ROWS', len(rows), 'SAMPLE', json.dumps(dict(rows[0]), default=str))
        return rows

    def assertMean(self, actual, values):
        expected = Decimal(sum(values)) / Decimal(len(values))
        self.assertLess(abs(actual - expected), Decimal('0.000000000001'))

    def test_daily_summary(self):
        rows = self.rows('vw_daily_temperature_summary', 'observation_date, location_name, environment')
        self.assertEqual(len(rows), len(self.daily))
        self.assertEqual(sum(r['reading_count'] for r in rows), len(self.source))
        seen = set()
        for r in rows:
            key = (r['observation_date'], r['location_name'], r['environment'])
            self.assertNotIn(key, seen)
            seen.add(key)
            values = self.daily[key]
            self.assertEqual((r['min_temperature'], r['max_temperature'], r['temperature_range'], r['reading_count']),
                             (min(values), max(values), max(values)-min(values), len(values)))
            self.assertMean(r['avg_temperature'], values)

    def test_hourly_coverage(self):
        rows = self.rows('vw_hourly_sampling_coverage', 'observation_date, observation_hour, location_name, environment')
        self.assertEqual(len(rows), len(self.hourly))
        self.assertEqual(sum(r['reading_count'] for r in rows), len(self.source))
        seen = set()
        for r in rows:
            hour = datetime.combine(r['observation_date'], time(r['observation_hour']))
            key = (hour, r['location_name'], r['environment'])
            self.assertNotIn(key, seen)
            seen.add(key)
            values = self.hourly[key]
            minutes = len({d.replace(second=0, microsecond=0) for d, _ in values})
            self.assertEqual(r['observed_minutes'], minutes)
            self.assertEqual(r['reading_count'], len(values))
            self.assertLess(abs(r['minute_coverage_pct'] - Decimal(minutes)*100/60), Decimal('0.000000000001'))
            self.assertEqual(r['has_unobserved_minutes'], minutes < 60)
            self.assertEqual(r['additional_readings_in_observed_minutes'], len(values)-minutes)

    def test_hourly_gap_without_multiplication(self):
        rows = self.rows('vw_hourly_indoor_outdoor_gap', 'observation_hour, location_name')
        expected = {(hour, local) for hour, local, env in self.hourly
                    if (hour, local, 'In') in self.hourly and (hour, local, 'Out') in self.hourly}
        self.assertEqual({(r['observation_hour'], r['location_name']) for r in rows}, expected)
        self.assertEqual(len(rows), len(expected))
        for r in rows:
            key = (r['observation_hour'], r['location_name'])
            inside = [t for _, t in self.hourly[(*key, 'In')]]
            outside = [t for _, t in self.hourly[(*key, 'Out')]]
            self.assertEqual(r['indoor_reading_count'], len(inside))
            self.assertEqual(r['outdoor_reading_count'], len(outside))
            self.assertMean(r['indoor_avg_temperature'], inside)
            self.assertMean(r['outdoor_avg_temperature'], outside)
            self.assertEqual(r['outdoor_minus_indoor'], r['outdoor_avg_temperature']-r['indoor_avg_temperature'])

    def test_source_integrity(self):
        self.assertEqual(len(self.source), 97605)
        self.assertEqual(len({r[0] for r in self.source}), 97605)
        self.assertEqual(sha256(CSV.read_bytes()).hexdigest(), OFFICIAL_HASH)


if __name__ == '__main__':
    unittest.main(verbosity=2)
