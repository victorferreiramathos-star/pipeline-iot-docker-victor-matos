"""Consultas somente de leitura e transformações do dashboard."""

from datetime import datetime, timezone

import pandas as pd
from sqlalchemy import text

from src.ingest import database_engine

VIEWS = {
    'daily': ('vw_daily_temperature_summary', 'observation_date, location_name, environment'),
    'coverage': ('vw_hourly_sampling_coverage', 'observation_date, observation_hour, location_name, environment'),
    'gap': ('vw_hourly_indoor_outdoor_gap', 'observation_hour, location_name'),
}


def read_views():
    """Snapshot consistente, transação READ ONLY e limite de tempo no servidor."""
    engine = database_engine()
    try:
        with engine.connect() as conn, conn.begin():
            conn.execute(text('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY'))
            conn.execute(text("SET LOCAL statement_timeout = '15s'"))
            frames = {key: pd.read_sql_query(text(f'SELECT * FROM iot.{view} ORDER BY {order}'), conn)
                      for key, (view, order) in VIEWS.items()}
        for key in ('daily', 'coverage'):
            frames[key]['observation_date'] = pd.to_datetime(frames[key]['observation_date'])
        frames['gap']['observation_hour'] = pd.to_datetime(frames['gap']['observation_hour'])
        coverage = frames['coverage']
        coverage['hour_timestamp'] = coverage['observation_date'] + pd.to_timedelta(coverage['observation_hour'], unit='h')
        return frames, datetime.now(timezone.utc).isoformat(timespec='seconds')
    finally:
        engine.dispose()


def filter_frames(frames, start, end, environments):
    """Período inclusivo por dia; comparação exige In e Out selecionados."""
    start, end = pd.Timestamp(start), pd.Timestamp(end) + pd.Timedelta(days=1)
    result = {}
    for key, frame in frames.items():
        column = 'observation_hour' if key == 'gap' else 'observation_date'
        mask = (frame[column] >= start) & (frame[column] < end)
        if key != 'gap':
            mask &= frame['environment'].isin(environments)
        elif not {'In', 'Out'}.issubset(environments):
            mask &= False
        result[key] = frame.loc[mask].copy()
    return result


def indicators(daily):
    count = int(daily['reading_count'].sum())
    if not count:
        return dict(count=0, minimum=None, maximum=None, mean=None)
    return dict(count=count, minimum=float(daily['min_temperature'].min()),
                maximum=float(daily['max_temperature'].max()),
                mean=float((daily['avg_temperature'] * daily['reading_count']).sum() / count))
