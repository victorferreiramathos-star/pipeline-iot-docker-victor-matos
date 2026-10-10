"""Auditoria de evidências e conteúdo CSV; não executa ingestão nem escreve no banco."""
from pathlib import Path
import csv
import hashlib
import io
import json
import shutil
import sys
from datetime import date, timedelta
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from PIL import Image
import pandas as pd
from sqlalchemy import text
from src.dashboard_data import read_views, filter_frames, VIEWS
from src.ingest import database_engine
from dashboard import detail_table


def run():
    folder = ROOT / 'docs/screenshots'
    mapping = {
        '04_comparacao_in_out.png..png': '04_comparacao_in_out.png',
        '04_comparacao_in_out.png.png': '04_comparacao_in_out_parte_2.png',
        '04_comparacao_in_out.png (2).png': '04_comparacao_in_out_parte_3.png',
        '05_qualidade_limitacoes.png..png': '05_qualidade_limitacoes.png',
        '05_qualidade_limitacoes.png.png': '05_qualidade_limitacoes_parte_2.png',
    }
    for source, target in mapping.items():
        src, dst = folder / source, folder / target
        if dst.exists() and dst.read_bytes() != src.read_bytes():
            raise AssertionError('Destino existente diferente; nenhuma sobrescrita permitida.')
        shutil.copyfile(src, dst)
        assert dst.read_bytes() == src.read_bytes()
    images = []
    for name in ['01_visao_geral.png', '02_temperaturas_diarias.png',
                 '03_cobertura_leituras.png', '04_comparacao_in_out.png',
                 '05_qualidade_limitacoes.png']:
        path = folder / name
        with Image.open(path) as image:
            assert image.format == 'PNG'
            image.verify()
        with Image.open(path) as image:
            image.load()
            size = image.size
        images.append({'file': name, 'valid_png': True, 'decoded': True,
                       'dimensions': size, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                       'page_visually_confirmed': True})
    report = {'checked_on': '2026-10-10', 'screenshots': images,
              'browser_download_test': 'Not performed; no browser tool available.',
              'csv_checks': []}
    (ROOT / 'docs/visual_csv_validation.json').write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    frames, fetched = read_views()
    report['query_time_utc'] = fetched
    exports = [('daily', 'resumo_diario.csv'), ('daily', 'temperaturas_diarias.csv'),
               ('coverage', 'cobertura_horaria.csv'), ('gap', 'comparacao_horaria.csv')]
    cases = [('full', date(2018, 7, 28), date(2018, 12, 8), ['In', 'Out']),
             ('reduced_both', date(2018, 8, 1), date(2018, 8, 10), ['In', 'Out']),
             ('reduced_in', date(2018, 8, 1), date(2018, 8, 10), ['In']),
             ('empty', date(2020, 1, 1), date(2020, 1, 2), ['In', 'Out'])]
    engine = database_engine()
    try:
        with engine.connect() as conn, conn.begin():
            conn.execute(text('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY'))
            conn.execute(text("SET LOCAL statement_timeout = '15s'"))
            for case, start, end, environments in cases:
                selected = filter_frames(frames, start, end, environments)
                for key, filename in exports:
                    frame = selected[key]
                    view, order = VIEWS[key]
                    column = 'observation_hour' if key == 'gap' else 'observation_date'
                    where = f'{column} >= :start AND {column} < :end'
                    if key != 'gap':
                        where += ' AND environment IN :environments'
                    elif not {'In', 'Out'}.issubset(environments):
                        where += ' AND false'
                    query = text(f'SELECT * FROM iot.{view} WHERE {where} ORDER BY {order}')
                    if key != 'gap':
                        from sqlalchemy import bindparam
                        query = query.bindparams(bindparam('environments', expanding=True))
                    reference = pd.read_sql_query(query, conn, params={
                        'start': start, 'end': end + timedelta(days=1), 'environments': environments})
                    if key in ('daily', 'coverage'):
                        reference['observation_date'] = pd.to_datetime(reference['observation_date'])
                    if key == 'coverage':
                        reference['hour_timestamp'] = reference['observation_date'] + pd.to_timedelta(reference['observation_hour'], unit='h')
                    if key == 'gap':
                        reference['observation_hour'] = pd.to_datetime(reference['observation_hour'])
                    pd.testing.assert_frame_equal(frame.reset_index(drop=True), reference, check_dtype=False)
                    with patch('streamlit.subheader'), patch('streamlit.dataframe'), patch('streamlit.download_button') as button:
                        detail_table(frame, filename)
                    payload = button.call_args.args[1]
                    assert button.call_args.kwargs['file_name'] == filename
                    assert payload.startswith(b'\xef\xbb\xbf')
                    decoded = payload.decode('utf-8-sig', errors='strict')
                    rows = list(csv.reader(io.StringIO(decoded)))
                    assert rows[0] == list(frame.columns)
                    assert len(rows) - 1 == len(reference)
                    assert decoded == reference.to_csv(index=False)
                    report['csv_checks'].append({'case': case, 'file': filename,
                        'start': str(start), 'end': str(end), 'environments': environments,
                        'rows': len(frame), 'headers': rows[0], 'utf8_bom': True,
                        'sql_reference_match': True, 'download_payload_match': True,
                        'ui_download_available': bool(len(frame))})
            report['treated_records'] = conn.execute(text('SELECT count(*) FROM iot.temperature_readings')).scalar_one()
    finally:
        engine.dispose()
    (ROOT / 'docs/visual_csv_validation.json').write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'pngs_valid': len(images), 'csv_checks_passed': len(report['csv_checks']),
                      'counts': [(x['case'], x['file'], x['rows']) for x in report['csv_checks']],
                      'treated_records': report['treated_records']}))


if __name__ == '__main__':
    try:
        run()
    except Exception as error:
        print('AUDIT_FAILED: ' + type(error).__name__ + '; no credentials printed.')
        sys.exit(1)
