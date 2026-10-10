"""Validação real de consultas, indicadores, filtros e páginas Streamlit."""

from datetime import date
import json
from unittest.mock import patch
import unittest

import streamlit as st
from streamlit.testing.v1 import AppTest
from sqlalchemy import text

from src.dashboard_data import filter_frames, indicators, read_views
from src.ingest import ROOT, database_engine


class DashboardTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.frames, cls.fetched_at = read_views()

    def test_01_queries_and_full_indicators(self):
        self.assertEqual({k: len(v) for k, v in self.frames.items()},
                         {'daily': 158, 'coverage': 2287, 'gap': 865})
        metrics = indicators(self.frames['daily'])
        engine = database_engine()
        try:
            with engine.connect() as conn, conn.begin():
                conn.execute(text('SET TRANSACTION READ ONLY'))
                reference = conn.execute(text('''SELECT count(*) AS count,
                    min(temperature) AS minimum, max(temperature) AS maximum,
                    avg(temperature) AS mean FROM iot.temperature_readings''')).mappings().one()
                self.assertEqual(metrics['count'], reference['count'])
                self.assertEqual(metrics['minimum'], reference['minimum'])
                self.assertEqual(metrics['maximum'], reference['maximum'])
                self.assertAlmostEqual(metrics['mean'], float(reference['mean']), places=10)
        finally:
            engine.dispose()
        print('INDICADORES_BANCO', metrics, flush=True)
        print('LINHAS_VIEWS', {k: len(v) for k, v in self.frames.items()}, flush=True)

    def test_02_filtered_indicators_and_empty(self):
        selected = filter_frames(self.frames, date(2018, 8, 1), date(2018, 8, 10), ['In'])
        metrics = indicators(selected['daily'])
        self.assertTrue(selected['gap'].empty)
        engine = database_engine()
        try:
            with engine.connect() as conn, conn.begin():
                conn.execute(text('SET TRANSACTION READ ONLY'))
                r = conn.execute(text('''SELECT count(*), min(temperature), max(temperature), avg(temperature)
                    FROM iot.temperature_readings WHERE observed_at >= :start AND observed_at < :end
                    AND environment = :env'''), {'start': date(2018, 8, 1), 'end': date(2018, 8, 11), 'env': 'In'}).one()
                self.assertEqual(metrics['count'], r[0])
                self.assertEqual(metrics['minimum'], r[1])
                self.assertEqual(metrics['maximum'], r[2])
                self.assertAlmostEqual(metrics['mean'], float(r[3]), places=10)
        finally:
            engine.dispose()
        for envs, start, end in [([], date(2018, 7, 28), date(2018, 12, 8)),
                                  (['In', 'Out'], date(2020, 1, 1), date(2020, 1, 2))]:
            frames = filter_frames(self.frames, start, end, envs)
            self.assertTrue(all(f.empty for f in frames.values()))
            self.assertEqual(indicators(frames['daily']), dict(count=0, minimum=None, maximum=None, mean=None))
        print('INDICADORES_FILTRO_IN_01_10_AGOSTO', metrics, flush=True)

    def test_03_all_pages(self):
        app = AppTest.from_file(str(ROOT / 'dashboard.py'), default_timeout=60).run()
        self.assertEqual(len(app.exception), 0)
        self.assertEqual(app.metric[0].value, '97.605')
        pages = list(app.radio[0].options)
        for page in pages:
            with self.subTest(page=page):
                app.radio[0].set_value(page).run()
                self.assertEqual(len(app.exception), 0)
                self.assertEqual(len(app.error), 0)
                if page != pages[-1]:
                    self.assertGreater(len(app.get('plotly_chart')), 0)
                    self.assertGreater(len(app.dataframe), 0)
                    self.assertGreater(len(app.get('download_button')), 0)
                if page == 'Temperaturas diárias':
                    spec = json.loads(app.get('plotly_chart')[-1].proto.spec)
                    self.assertEqual(spec['layout']['legend']['title']['text'], 'Ambiente, Extremo')
                print('PAGINA_OK', page, flush=True)

    def test_04_ui_empty_and_single_environment(self):
        app = AppTest.from_file(str(ROOT / 'dashboard.py'), default_timeout=60).run()
        app.multiselect[0].set_value([]).run()
        self.assertEqual(len(app.exception), 0)
        self.assertEqual(app.metric[0].value, '0')
        self.assertGreater(len(app.info), 0)
        app.multiselect[0].set_value(['In']).run()
        app.radio[0].set_value('Comparação In/Out').run()
        self.assertEqual(len(app.exception), 0)
        self.assertGreater(len(app.info), 0)
        app.multiselect[0].set_value(['In', 'Out']).run()
        app.date_input[0].set_value((date(2020, 1, 1), date(2020, 1, 2))).run()
        self.assertEqual(len(app.exception), 0)
        self.assertEqual(app.metric[0].value, '0')

    def test_05_connection_error_is_safe(self):
        st.cache_data.clear()
        with patch('src.dashboard_data.read_views', side_effect=RuntimeError('TEST_SECRET_MUST_NOT_APPEAR')):
            app = AppTest.from_file(str(ROOT / 'dashboard.py'), default_timeout=60).run()
            self.assertEqual(len(app.exception), 0)
            self.assertEqual(len(app.error), 1)
            self.assertNotIn('TEST_SECRET', app.error[0].value)
        st.cache_data.clear()


if __name__ == '__main__':
    unittest.main(verbosity=2)
