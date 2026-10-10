# Pipeline de Dados com IoT e Docker

**Aluno:** Victor Matos  
**Disciplina:** Disruptive Architectures: IoT, Big Data e IA

## Objetivo

Construir um pipeline em Python para processar leituras reais de temperatura de dispositivos IoT, armazená-las no PostgreSQL e apresentar análises em um dashboard Streamlit.

## Estado atual

Ingestão, três views e dashboard Streamlit implementados. O dashboard consulta somente as views reais e não altera registros. As cinco páginas possuem capturas reais em `docs/screenshots`, e o [relatório acadêmico final](docs/relatorio_final_victor_matos.pdf) contém 30 páginas revisadas, com cinco capturas principais e oito complementares. Os quatro CSVs passaram em 16 verificações automatizadas; o download e a abertura manual pelo navegador continuam pendentes.

## Tecnologias

- Python e pandas para processamento dos dados.
- SQLAlchemy e psycopg2-binary para acesso ao PostgreSQL.
- PostgreSQL 16 em Docker, com Docker Compose.
- Streamlit e Plotly para visualizações interativas.

## Estrutura

```text
Projeto_Pipeline_VicMatos/
├── .env.example
├── .gitignore
├── README.md
├── requirements.txt
├── docker-compose.yml
├── dashboard.py
├── src/
│   ├── __init__.py
│   └── ingest.py
├── sql/
│   └── views.sql
├── data/
├── docs/
│   └── screenshots/
└── tests/
```

`src/` contém a ingestão e as consultas/transformações do dashboard (`dashboard_data.py`); `sql/`, as views; `data/`, a base real; `docs/`, o relatório e as evidências técnicas; `docs/screenshots/`, as cinco capturas principais e suas complementares reais; e `tests/` contém testes de ingestão, views e dashboard. `.streamlit/config.toml` define o tema visual e desativa o envio de estatísticas de uso.

## Dados

Fonte: [Temperature Readings: IoT Devices, no Kaggle](https://www.kaggle.com/datasets/atulanandjha/temperature-readings-iot-devices). O arquivo original `data/IOT-temp.csv` contém 97.606 linhas e uma duplicata exata. A ingestão verifica seu SHA-256 antes de carregar. Nenhum registro do CSV é modificado.

## Configuração prevista

O arquivo `.env.example` documenta as variáveis de ambiente. A instalação local já utiliza `.env` com credenciais próprias. Em outra máquina, crie sua cópia local e defina uma senha própria para `POSTGRES_PASSWORD`. Não publique esse arquivo.

O Compose prepara PostgreSQL 16 com volume persistente, healthcheck e porta local configurável por `POSTGRES_PORT` (padrão 5432). A porta é vinculada a `127.0.0.1`. Aplicações executadas no Windows usarão `POSTGRES_HOST=localhost`.

Em uma instalação nova, copie `.env.example` para `.env` **somente se o arquivo local ainda não existir**, edite a senha local e mantenha o arquivo fora do Git. Com Docker Desktop em execução e contexto `desktop-linux` disponível:

```powershell
docker --context desktop-linux compose config --quiet
docker --context desktop-linux compose up -d postgres
docker --context desktop-linux compose ps
```

Aguarde o estado `healthy` antes de executar ingestão ou dashboard. Após reiniciar esta máquina, o contêiner existente pode ser retomado com `docker --context desktop-linux start projeto_pipeline_vicmatos-postgres-1`, preservando o volume. Não remova o volume para reiniciar o projeto. O `.env.example` não contém senha utilizável: a configuração precisa de uma senha local definida.

## Executar a ingestão

Com PostgreSQL deste projeto disponível e `.env` local configurado:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install pandas sqlalchemy psycopg2-binary
.\.venv\Scripts\python.exe -m src.ingest
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

As três bibliotecas já constam de `requirements.txt`; não é preciso instalar as bibliotecas do dashboard nesta etapa. Execute os comandos na raiz do projeto. As credenciais são lidas exclusivamente do `.env`, sem usar variáveis globais ou imprimi-las.

A carga cria `audit.ingestion_runs`, `audit.ingestion_rejections`, `staging.temperature_raw` e `iot.temperature_readings`. Staging preserva nomes e valores originais, com número da linha e identificador da execução. Datas usam `%d-%m-%Y %H:%M`; temperaturas precisam ser inteiras representáveis em SMALLINT; ambientes aceitos: `In` e `Out`. Não se assume unidade térmica ou fuso não documentado.

Cada execução bem-sucedida preserva todas as linhas no staging, contabiliza duplicatas exatas e registra rejeições com motivos. Identificadores conflitantes são rejeitados; observações simultâneas com IDs distintos são preservadas. A tabela tratada usa o ID original como chave primária. Reexecutar o arquivo não duplica leituras tratadas, embora gere nova trilha de auditoria e staging.

A reconciliação é: **origem = duplicatas + rejeições + inseridos + já existentes**. Um bloqueio transacional serializa as cargas. DDL, staging, rejeições, dados tratados e conclusão da auditoria são confirmados juntos; falhas técnicas revertem a execução inteira, inclusive seu registro de auditoria. A linha de comando retorna erro sem revelar detalhes sensíveis. Cargas técnicas que falham não deixam registro persistente de falha nesta versão.

Os testes executam duas cargas oficiais e verificam conteúdo integral, auditoria e idempotência. Casos inválidos e conflitos usam cópias em memória de registros reais, dentro de transações revertidas; não alteram o CSV nem deixam dados de teste no banco. Use exclusivamente o banco deste projeto.

## Views analíticas

As views pertencem ao schema `iot`. Para aplicar suas definições em uma única transação, com o banco deste projeto disponível:

```powershell
.\.venv\Scripts\python.exe -c "from src.ingest import database_engine, ROOT; e=database_engine(); c=e.connect(); t=c.begin(); c.exec_driver_sql((ROOT/'sql/views.sql').read_text(encoding='utf-8')); t.commit(); c.close(); e.dispose()"
.\.venv\Scripts\python.exe -m unittest discover -s tests -p test_views.py -v
```

O segundo comando testa apenas as views; não reexecuta a ingestão. `CREATE OR REPLACE VIEW` permite reaplicar definições compatíveis. Mudanças incompatíveis de nomes ou tipos exigem uma migração analisada separadamente, sem exclusão automática.

| View | Colunas | Propósito |
|---|---|---|
| `iot.vw_daily_temperature_summary` | `observation_date`, `location_name`, `environment`, `min_temperature`, `max_temperature`, `avg_temperature`, `temperature_range`, `reading_count` | Resumir extremos, média, amplitude e volume de leituras por dia, local e ambiente. |
| `iot.vw_hourly_sampling_coverage` | `observation_date`, `observation_hour`, `location_name`, `environment`, `reading_count`, `observed_minutes`, `minute_coverage_pct`, `has_unobserved_minutes`, `additional_readings_in_observed_minutes` | Mostrar frequência de coleta e concentração de leituras em minutos observados. |
| `iot.vw_hourly_indoor_outdoor_gap` | `observation_hour`, `location_name`, `indoor_avg_temperature`, `outdoor_avg_temperature`, `outdoor_minus_indoor`, `indoor_reading_count`, `outdoor_reading_count` | Comparar médias de ambientes em horas com ambos disponíveis. Aqui `observation_hour` é um timestamp truncado à hora; na view de cobertura é um inteiro de 0 a 23, acompanhado da data. |

`minute_coverage_pct = observed_minutes * 100 / 60`: representa minutos distintos com registros, **não disponibilidade real ou uptime do sensor**. Horas com menos de 60 minutos observados recebem `has_unobserved_minutes=true`; esse sinal descreve a amostragem, sem provar falha. `additional_readings_in_observed_minutes` conta leituras além da primeira em cada minuto, sem classificá-las como duplicatas. Não são geradas horas nem medições ausentes. Horas nas extremidades do período também usam denominador 60, portanto podem ter cobertura parcial pela própria janela do arquivo.

A diferença é **média externa menos média interna**: positiva indica média externa maior. As duas médias são calculadas separadamente por local e hora, antes da subtração, sem JOIN entre observações brutas. Horas com apenas um ambiente são excluídas da comparação. As leituras não são necessariamente simultâneas dentro da hora, nem têm frequências iguais; a diferença não estabelece causalidade.

As médias são ponderadas por leituras, não pelo tempo transcorrido. O dataset identifica um local (`Room Admin`) e ambientes `In`/`Out`, mas **não identifica sensores físicos individuais**. A unidade térmica e o fuso horário não foram confirmados: não rotular como graus Celsius nem converter fusos sem evidência da fonte. Não há arredondamento no SQL; a apresentação poderá arredondar os resultados depois.

As views não definem ordenação. Exemplos de consultas de validação ordenadas:

```sql
SELECT * FROM iot.vw_daily_temperature_summary
ORDER BY observation_date, location_name, environment LIMIT 5;
SELECT * FROM iot.vw_hourly_sampling_coverage
ORDER BY observation_date, observation_hour, location_name, environment LIMIT 5;
SELECT * FROM iot.vw_hourly_indoor_outdoor_gap
ORDER BY observation_hour, location_name LIMIT 5;
```

Os testes comparam todos os grupos das views com agregações independentes em Python sobre as leituras reais, conferem médias, extremos, contagens, minutos distintos, sinal da diferença, unicidade dos grupos e ausência de multiplicação. Também verificam os 97.605 IDs únicos e o SHA-256 original do CSV. As consultas de teste são somente de leitura, em snapshot consistente.

Validação real: 158 linhas no resumo diário, 2.287 na cobertura e 865 na comparação horária; quatro testes aprovados. A tabela manteve 97.605 registros e fingerprint idêntico antes/depois da criação das views. Consultas independentes, amostras reais e limitações estão em [docs/views_validation.md](docs/views_validation.md).

## Dashboard — IoT Thermal Analytics | Victor Matos

Instale as dependências apenas no ambiente virtual do projeto e execute na raiz:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run dashboard.py --server.address 127.0.0.1 --server.port 8501 --server.headless true --browser.gatherUsageStats false
```

Abra `http://127.0.0.1:8501`. O PostgreSQL deste projeto precisa estar disponível; credenciais são lidas exclusivamente do `.env` local. O dashboard não inicia contêineres, não aplica views e não executa ingestão.

A navegação oferece Visão geral, Temperaturas diárias, Cobertura das leituras, Comparação In/Out e Qualidade e limitações dos dados. Filtros de período são inclusivos por dia, e a seleção de ambientes controla os indicadores. A comparação exige ambos os ambientes. Seleções vazias e períodos sem dados mostram mensagens, sem inventar registros.

Os indicadores de mínimo e máximo vêm dos extremos das views diárias; a média é `sum(média_do_grupo * contagem_do_grupo) / sum(contagem_do_grupo)`, ponderada por registros. Não é a média simples das médias. Na página de comparação, os indicadores superiores continuam descrevendo todos os registros dos filtros; o gráfico usa apenas horas com ambos os ambientes.

Gráficos Plotly: evolução diária das médias, mínimas/máximas diárias, quantidade de leituras por ambiente, cobertura de minutos por hora e diferença horária externa menos interna. As páginas analíticas possuem tabela detalhada filtrada e download CSV. O download contém agregações das views, não as linhas brutas do dataset. A página de qualidade explica as limitações, sem transformar ausência de observação em falha do sensor.

As três views são lidas numa transação consistente `READ ONLY`, com limite de 15 segundos por consulta. O cache expira em 60 segundos; **Atualizar dados** invalida o cache imediatamente. A hora de consulta é apresentada em UTC, sem atribuir esse fuso às observações. Se a conexão falhar, a interface oferece orientação sem mostrar exceções ou credenciais. Em cache, o snapshot anterior pode continuar visível por até 60 segundos.

Testes exclusivos do dashboard, sem repetir ingestão nem modificar as views:

```powershell
.\.venv\Scripts\python.exe -B -m unittest discover -s tests -p test_dashboard.py -v
```

O dataset não identifica sensores individuais. Unidade térmica e fuso não foram confirmados; temperaturas não são rotuladas em Celsius. Cobertura mede minutos com registros, não disponibilidade comprovada. Médias horárias de In/Out não implicam simultaneidade ou causalidade.

Evidências reais: [docs/dashboard_validation.md](docs/dashboard_validation.md), saída dos cinco testes em `docs/dashboard_test_results.txt` e verificação HTTP/integridade em `docs/dashboard_http_validation.json`. Todas as páginas foram exercitadas por AppTest. Em 10/10/2026, o usuário confirmou a revisão visual manual das cinco páginas, sem problemas relevantes. O agente conferiu os cinco PNGs, suas páginas e a incorporação das imagens ao PDF. Nenhuma captura fictícia foi criada. Resultados de execução são históricos e não garantem que os serviços estejam ativos após reiniciar o computador.

| Página | Captura real |
|---|---|
| Visão geral | [01_visao_geral.png](docs/screenshots/01_visao_geral.png) |
| Temperaturas diárias | [02_temperaturas_diarias.png](docs/screenshots/02_temperaturas_diarias.png) |
| Cobertura das leituras | [03_cobertura_leituras.png](docs/screenshots/03_cobertura_leituras.png) |
| Comparação In/Out | [04_comparacao_in_out.png](docs/screenshots/04_comparacao_in_out.png) |
| Qualidade e limitações | [05_qualidade_limitacoes.png](docs/screenshots/05_qualidade_limitacoes.png) |

Capturas complementares e hashes estão no [inventário visual](docs/screenshots/README.md). Os [resultados de exportação CSV](docs/visual_csv_validation.json) confirmam UTF-8 com BOM, cabeçalhos, contagens e filtros contra consultas independentes. Falta conferir manualmente os quatro downloads no navegador.

Os dados mostram amostragem irregular: 2.265 dos 2.287 grupos horários possuem menos de 60 minutos observados. Isso não comprova indisponibilidade do sensor. As 865 horas com ambos os ambientes permitem analisar a diferença externa menos interna; médias por registros não garantem simultaneidade ou causalidade. Insights e aplicações propostas estão no [relatório](docs/relatorio_final_victor_matos.md).

## Versionamento e conferência final

Comandos já utilizados nesta máquina: `git --version`, `git init -b main`, configuração **local** da identidade de Victor Matos, `git status`, `git check-ignore` e `git ls-files`. Não houve commits, push ou publicação, e não há remoto configurado no repositório local na conferência de 10/10/2026. Conectar o remoto e publicar continuam dependendo de autorização.

Para repetir apenas os testes de views e dashboard, sem gravar cargas no banco:

```powershell
.\.venv\Scripts\python.exe -B -m unittest discover -s tests -p 'test_[dv]*.py' -v
```

Não use o comando de descoberta de **todos** os testes quando a etapa permitir somente leitura: os testes de ingestão criam cargas de auditoria. A conferência final de 10/10/2026 executou nove testes de leitura com sucesso e confirmou 97.605 IDs únicos, fingerprint preservado e três cargas concluídas. Veja [docs/final_delivery_checklist.md](docs/final_delivery_checklist.md).

## Próximas entregas

- Manter as validações e a rastreabilidade da ingestão do CSV real.
- Manter as três views e seus testes de agregação.
- Manter o dashboard e seus testes de consultas e filtros.
- Completar as instruções de execução e registrar os comandos Git utilizados.
- Entregar o [PDF acadêmico concluído](docs/relatorio_final_victor_matos.pdf), com etapas, views, capturas reais e insights.
- Confirmar manualmente os downloads CSV no navegador.
- Preparar o vídeo pitch de até quatro minutos.
- Publicar o repositório e verificar os links somente mediante autorização.

Pastas vazias existem localmente, mas não são versionadas pelo Git até receberem arquivos.
