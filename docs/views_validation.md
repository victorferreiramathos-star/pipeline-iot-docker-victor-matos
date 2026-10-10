# Validação real das views — Victor Matos

Executada em 08/10/2026 no PostgreSQL deste projeto, contexto Docker `desktop-linux`.

## Estrutura inspecionada

`iot.temperature_readings`: `source_id text`, `location_name text`,
`observed_at timestamp without time zone`, `temperature smallint`,
`environment text`, `run_id uuid`.

## Integridade

Antes e depois da criação das views, em uma mesma transação com bloqueio SHARE
na tabela: 97.605 registros. O fingerprint do conteúdo completo foi idêntico:
`db628f44918517e86003d1e23d9bcb7b`.

Consulta utilizada:

```sql
SELECT count(*) AS total,
       md5(string_agg(to_jsonb(t)::text, '' ORDER BY source_id)) AS content_fingerprint
FROM iot.temperature_readings t;
```

O fingerprint é uma comparação de conteúdo antes/depois, não uma assinatura de
segurança. O teste do arquivo verificou separadamente o SHA-256 do CSV original.

## Contagens reais

| View | Linhas |
|---|---:|
| `iot.vw_daily_temperature_summary` | 158 |
| `iot.vw_hourly_sampling_coverage` | 2.287 |
| `iot.vw_hourly_indoor_outdoor_gap` | 865 |

A soma das contagens de leituras nas views diária e de cobertura é 97.605 em
cada uma. A view de comparação exclui horas sem os dois ambientes.

Há 2.265 grupos horários com menos de 60 minutos observados e 717 grupos com
leituras adicionais em minutos já observados. Não são evidências de defeito,
duplicidade ou disponibilidade real de sensores.

## Amostras conferidas por consultas independentes

Local `Room Admin`:

- Dia 28/07/2018, `In`: mínimo 31, máximo 31, média 31, amplitude 0 e 45 leituras.
- Hora 28/07/2018 07:00, `In`: 45 leituras, 7 minutos distintos,
  cobertura de 11,6666666666666667% e 38 leituras adicionais em minutos observados.
- Mesma hora: `In` tem soma 1.395 e 45 leituras (média 31);
  `Out` tem soma 1.367 e 43 leituras (média 31,7906976744186047).
  Diferença externa menos interna: 0,7906976744186047.

Consultas de conferência diretamente na tabela, sem usar as views como fonte:

```sql
SELECT MIN(temperature), MAX(temperature), AVG(temperature),
       MAX(temperature)-MIN(temperature) AS amplitude, COUNT(*)
FROM iot.temperature_readings
WHERE observed_at >= '2018-07-28' AND observed_at < '2018-07-29'
  AND location_name='Room Admin' AND environment='In';

SELECT COUNT(*), COUNT(DISTINCT EXTRACT(MINUTE FROM observed_at)) AS minutes,
       COUNT(DISTINCT EXTRACT(MINUTE FROM observed_at))*100.0/60 AS coverage
FROM iot.temperature_readings
WHERE observed_at >= '2018-07-28 07:00' AND observed_at < '2018-07-28 08:00'
  AND location_name='Room Admin' AND environment='In';

SELECT environment, SUM(temperature), COUNT(*),
       SUM(temperature)::numeric/COUNT(*) AS independent_average
FROM iot.temperature_readings
WHERE observed_at >= '2018-07-28 07:00' AND observed_at < '2018-07-28 08:00'
  AND location_name='Room Admin'
GROUP BY environment ORDER BY environment;
```

## Testes

Comando: `.\.venv\Scripts\python.exe -B -m unittest discover -s tests -p test_views.py -v`.

Resultado observado: **4 testes aprovados em 10,033 segundos**:

- Resumo diário: todos os grupos, extremos, amplitude, médias e reconciliação.
- Cobertura horária: todos os grupos, minutos distintos, percentual e indicadores.
- Comparação horária: grupos elegíveis, médias, contagens, diferença e unicidade.
- Integridade: 97.605 IDs únicos e SHA-256 original do CSV.

O oracle dos testes agrega as linhas reais em Python, independentemente do SQL
das views. Nenhuma carga de ingestão foi repetida nesta etapa. Não houve erros
nos comandos de aplicação ou nos testes.

## Limitações

Não há identificação de sensores físicos individuais, confirmação da unidade
térmica ou do fuso. As médias são por registro e não por duração. Cobertura mede
minutos com registros, com denominador 60 inclusive nas horas nas extremidades
do arquivo. Ausência de registros não permite afirmar indisponibilidade do sensor.
As comparações horárias não garantem simultaneidade de cada observação.
