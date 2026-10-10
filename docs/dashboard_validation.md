# Validação do dashboard — Victor Matos

Data: 08/10/2026. Aplicação: **IoT Thermal Analytics | Victor Matos**.

## Execução local real

- Endereço: http://127.0.0.1:8501 (somente interface local).
- Processo iniciado: PID 18440, usando Python do `.venv` do projeto.
- Streamlit 1.65.0; Plotly 7.1.0.
- Página raiz: HTTP 200.
- Endpoint `/_stcore/health`: HTTP 200, resposta `ok`.
- O processo pode ser encerrado ao fechar a sessão ou reiniciar o Windows;
  o comando de inicialização está no README.

Resultados HTTP e integridade estão em `dashboard_http_validation.json`.
Saída e erros do servidor estão em `dashboard_server.stdout.txt` e
`dashboard_server.stderr.txt`. São logs reais, não capturas de tela.

## Testes reais

Comando: `.\.venv\Scripts\python.exe -B -m unittest discover -s tests -p test_dashboard.py -v`.

Resultado final: **5 testes aprovados em 13,283 segundos**, código de saída 0.
A suíte foi repetida para registrar a saída em UTF-8 corretamente. A primeira
execução também passou. Saída final: `dashboard_test_results.txt`.

1. Consultas das três views e comparação dos indicadores globais com SQL direto.
2. Indicadores filtrados por período/ambiente e seleções vazias.
3. Navegação das cinco páginas com Streamlit AppTest, sem exceções; presença de
   gráficos, tabelas e controles de download nas quatro páginas analíticas.
4. Interface com nenhum ambiente selecionado, somente In na comparação e período sem dados.
5. Falha de conexão simulada, exibindo mensagem segura sem revelar o conteúdo da exceção.

AppTest executou os componentes e callbacks do Streamlit com dados reais do
PostgreSQL. Não equivale a uma revisão visual em navegador nem testa todos os
gestos de interação do Plotly. Não foram geradas capturas de tela.

## Indicadores conferidos com o banco

| Filtro | Registros | Mínimo | Máximo | Média ponderada por registros |
|---|---:|---:|---:|---:|
| Todos os dados, In e Out | 97.605 | 21 | 51 | 35,0538599456995 |
| 01/08/2018 a 10/08/2018, In | 575 | 27 | 30 | 28,601739130434783 |

Consultas às views retornaram 158 grupos diários, 2.287 grupos de cobertura e
865 grupos de comparação. Mínimo/máximo foram comparados com a tabela tratada;
médias globais e filtradas coincidiram com `AVG(temperature)` no SQL direto,
com tolerância de dez casas decimais.

## Integridade e segurança

- A aplicação consulta somente as três views, em transação READ ONLY e snapshot
  REPEATABLE READ, com statement timeout de 15 segundos.
- Cache de leitura: TTL de 60 segundos e botão de atualização explícita.
- A tabela permaneceu com 97.605 registros e fingerprint
  `db628f44918517e86003d1e23d9bcb7b`, igual ao registrado na etapa anterior.
- SHA-256 do CSV preservado:
  `2bf965701db96cd5788403d395a25d2dd7282bea24e317b7f7b157b7a02063d4`.
- `.env` e `.venv/` continuam ignorados; `.env` não está rastreado pelo Git.
- Não houve alterações na ingestão, nas views, nos dados ou em outros contêineres.
- Não houve commits, push ou publicação.

## Avisos e limitações

Os testes emitiram avisos de `ScriptRunContext` e cache em memória ao executar
fora de um servidor Streamlit. Não impediram os cinco testes. A simulação de
falha de conexão foi deliberada e não representa falha real do PostgreSQL.

Não há unidade térmica ou fuso confirmado, nem identificação de sensores
individuais. Cobertura significa minutos com registros; não uptime. Médias
são ponderadas por registros. Comparação exige ambos os ambientes na mesma
hora, sem garantir simultaneidade ou causalidade. Linhas dos gráficos conectam
observações disponíveis sem imputar medições. O cache pode apresentar o snapshot
anterior por até 60 segundos. Não foi feita revisão visual manual no navegador.
