-- Victor Matos: análises por local e ambiente, sem inferir sensores individuais.
-- Unidade térmica e fuso horário não confirmados na fonte.
-- Ordenar nas consultas consumidoras, nunca depender da ordem da view.

CREATE OR REPLACE VIEW iot.vw_daily_temperature_summary AS
SELECT observed_at::date AS observation_date,
       location_name,
       environment,
       MIN(temperature) AS min_temperature,
       MAX(temperature) AS max_temperature,
       AVG(temperature) AS avg_temperature,
       MAX(temperature) - MIN(temperature) AS temperature_range,
       COUNT(*) AS reading_count
FROM iot.temperature_readings
GROUP BY observed_at::date, location_name, environment;

-- Cobertura: minutos distintos com registros / 60; não é uptime do sensor.
-- Só retorna horas observadas. Múltiplas leituras no mesmo minuto são preservadas.
CREATE OR REPLACE VIEW iot.vw_hourly_sampling_coverage AS
SELECT observed_at::date AS observation_date,
       EXTRACT(HOUR FROM observed_at)::integer AS observation_hour,
       location_name,
       environment,
       COUNT(*) AS reading_count,
       COUNT(DISTINCT DATE_TRUNC('minute', observed_at)) AS observed_minutes,
       COUNT(DISTINCT DATE_TRUNC('minute', observed_at)) * 100.0 / 60
           AS minute_coverage_pct,
       COUNT(DISTINCT DATE_TRUNC('minute', observed_at)) < 60
           AS has_unobserved_minutes,
       COUNT(*) - COUNT(DISTINCT DATE_TRUNC('minute', observed_at))
           AS additional_readings_in_observed_minutes
FROM iot.temperature_readings
GROUP BY observed_at::date, EXTRACT(HOUR FROM observed_at)::integer,
         location_name, environment;

-- Agrega antes de comparar. Diferença positiva: média externa maior que interna.
-- Horas sem ambos os ambientes são excluídas, não preenchidas nem interpoladas.
CREATE OR REPLACE VIEW iot.vw_hourly_indoor_outdoor_gap AS
SELECT DATE_TRUNC('hour', observed_at) AS observation_hour,
       location_name,
       AVG(temperature) FILTER (WHERE environment = 'In') AS indoor_avg_temperature,
       AVG(temperature) FILTER (WHERE environment = 'Out') AS outdoor_avg_temperature,
       AVG(temperature) FILTER (WHERE environment = 'Out')
         - AVG(temperature) FILTER (WHERE environment = 'In') AS outdoor_minus_indoor,
       COUNT(*) FILTER (WHERE environment = 'In') AS indoor_reading_count,
       COUNT(*) FILTER (WHERE environment = 'Out') AS outdoor_reading_count
FROM iot.temperature_readings
GROUP BY DATE_TRUNC('hour', observed_at), location_name
HAVING COUNT(*) FILTER (WHERE environment = 'In') > 0
   AND COUNT(*) FILTER (WHERE environment = 'Out') > 0;
