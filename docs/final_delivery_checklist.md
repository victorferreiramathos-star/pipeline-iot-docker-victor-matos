# Checklist de evidências e entrega acadêmica — Victor Matos

Conferência: **10/10/2026**, America/Sao_Paulo.
Disciplina: Disruptive Architectures: IoT, Big Data e IA.

## Concluído

- Dataset oficial preservado: 97.606 registros originais, uma duplicata exata.
- Ingestão transacional com staging original, SHA-256, rejeições e reconciliação.
- Três execuções concluídas registradas no banco: 97.605 inseridos na primeira,
  nenhuma nova leitura tratada nas duas reexecuções.
- Tabela tratada: **97.605 registros e 97.605 IDs únicos**.
- Fingerprint atual: `db628f44918517e86003d1e23d9bcb7b`, igual às etapas anteriores.
- Staging: 292.818 linhas; rejeições persistentes: zero. Auditoria agregada:
  292.818 recebidos = 3 ocorrências da duplicata + 97.605 inseridos + 195.210 já existentes.
- Três views com 158, 2.287 e 865 linhas, conferidas com cálculos independentes.
- Dashboard de cinco páginas, filtros, gráficos, tabelas, exportação CSV e avisos.
- Nove testes atuais aprovados: cinco do dashboard e quatro das views,
  em 39,258 segundos. Conexões foram forçadas a somente leitura.
- Três testes de ingestão aprovados historicamente; não reexecutados nesta etapa,
  pois gravam cargas de auditoria e a autorização atual proíbe alterar o banco.
- Servidor local: página raiz HTTP 200; saúde HTTP 200 com `ok`.
- Revisão visual das cinco páginas concluída pelo usuário, sem problemas relevantes.
  O agente conferiu visualmente os cinco PNGs principais em 10/10/2026;
  todos passaram na validação de formato e decodificação.
- README explica instalação, configuração local, PostgreSQL, ingestão, views,
  dashboard, testes, limitações e comandos Git utilizados.
- Links locais dos arquivos Markdown examinados: nenhum destino inexistente.
- `.env` e `.venv/` ignorados; `.env` não rastreado.

## Evidências atuais

- [Relatório acadêmico final em PDF](relatorio_final_victor_matos.pdf): 30 páginas,
  revisadas após renderização, com cinco capturas principais e oito complementares.
- [Texto-fonte do relatório](relatorio_final_victor_matos.md).
- [Orientação original preservada](orientacao_academica_original.pdf): sete páginas,
  relidas; requisitos específicos do PDF confirmados na página 6.
- [Revisão técnica do PDF](pdf_review_validation.json): todas as páginas renderizadas,
  texto dentro dos limites e pixels das 13 imagens iguais aos PNGs originais.
- [Registro da revisão final](report_delivery_review.md).

- `final_evidence_tests.txt`: execução real dos nove testes.
- `final_integrity_check.json`: contagens, fingerprint, hash do CSV e HTTP atuais.
- `views_validation.md`: consultas independentes e resultados das views.
- `dashboard_validation.md`: validação técnica inicial.
- `dashboard_quality_audit.md`: auditoria anterior e correção de legenda.
- `dashboard_components_audit.json`: títulos, eixos, legendas e controles gerados.

Os documentos antigos representam suas datas de execução. Onde mencionam
revisão visual pendente, esta atualização de 10/10/2026 registra a confirmação
posterior do usuário; não altera o histórico das verificações realizadas.

## Capturas reais — atualização visual de 10/10/2026

- [x] [Visão geral](screenshots/01_visao_geral.png): página confirmada visualmente.
- [x] [Temperaturas diárias](screenshots/02_temperaturas_diarias.png): página confirmada visualmente.
- [x] [Cobertura das leituras](screenshots/03_cobertura_leituras.png): página confirmada visualmente.
- [x] [Comparação In/Out](screenshots/04_comparacao_in_out.png): página confirmada visualmente.
- [x] [Qualidade e limitações](screenshots/05_qualidade_limitacoes.png): página confirmada visualmente.

Foram organizadas treze imagens reais: cinco principais e oito complementares.
Os cinco novos arquivos enviados pelo usuário tinham extensões repetidas; foram
copiados para nomes padronizados, preservando os arquivos enviados e seus bytes.
Todos os cinco PNGs principais passaram por verificação de formato e decodificação
com Pillow, além da conferência visual de título, menu e conteúdo.
Origem: pasta Screenshots das Imagens do OneDrive da conta Jane. Foram pesquisados
o projeto e as pastas acessíveis Downloads, Imagens e Área de Trabalho, incluindo
as correspondentes no OneDrive, sem consultar projetos Felipe ou João.
Os menus selecionados e o conteúdo permitiram confirmar a página de cada imagem.
As cópias têm SHA-256 idêntico aos originais, que permaneceram no local de origem.
Veja o [registro visual](screenshots/README.md) e o
[inventário com hashes e origens](screenshots/evidence_inventory.json).

As capturas mostram trechos de páginas, com complementares para gráficos,
tabelas e avisos. Não houve montagem ou edição. Imagens estáticas não comprovam
download CSV ou interação. A etapa atual verificou o conteúdo gerado para os
downloads e consultou o banco somente em transações READ ONLY: 97.605 registros.
As cinco páginas e suas complementares foram incorporadas ao relatório acadêmico.

## Exportação CSV

Os testes confirmaram controles de download nas quatro páginas analíticas.
O código produz CSV UTF-8 com BOM a partir das tabelas filtradas das views:

| Página | Nome do download | Linhas com período completo e In/Out |
|---|---|---:|
| Visão geral | `resumo_diario.csv` | 158 |
| Temperaturas diárias | `temperaturas_diarias.csv` | 158 |
| Cobertura das leituras | `cobertura_horaria.csv` | 2.287 |
| Comparação In/Out | `comparacao_horaria.csv` | 865 |

Esses totais foram confirmados no conteúdo produzido pela função real de
exportação, interceptando a chamada ao botão; não são downloads pelo navegador.
A página de qualidade é explicativa e não exige download.

**Validação técnica atual: 16 verificações aprovadas.** Para cada um dos quatro
arquivos foram verificados cabeçalhos, UTF-8 estrito com BOM, número de registros
e igualdade do conteúdo com consultas SQL independentes e os filtros aplicados.

| Filtro | Resumo diário | Temperaturas diárias | Cobertura horária | Comparação horária |
|---|---:|---:|---:|---:|
| 28/07–08/12/2018, In e Out | 158 | 158 | 2.287 | 865 |
| 01–10/08/2018, In e Out | 3 | 3 | 7 | 3 |
| 01–10/08/2018, somente In | 1 | 1 | 3 | 0 |
| 01–02/01/2020, In e Out | 0 | 0 | 0 | 0 |

As datas finais são inclusivas. Contagens excluem o cabeçalho. Nos estados sem
dados o dashboard não oferece download; o teste apenas verificou a serialização
vazia da função. A comparação exige ambos os ambientes. A cobertura exporta
também `hour_timestamp`, coluna derivada no dashboard, conferida na referência.
Cabeçalhos completos e resultados estão em [visual_csv_validation.json](visual_csv_validation.json).
O procedimento reproduzível está em [verify_visual_csv.py](verify_visual_csv.py).
Não há ferramenta de navegador nesta sessão; o clique e a gravação no disco
continuam não verificados. Nenhuma credencial foi exibida ou registrada.

**Teste manual ainda sem confirmação:** clicar em cada download, conferir
nome, abrir o arquivo no Excel/LibreOffice/editor e verificar cabeçalhos,
acentuação, separadores, datas e contagem de linhas sem o cabeçalho. Repetir
com um filtro reduzido e comparar com a tabela exibida. Os arquivos usam vírgula
como delimitador; dependendo da configuração regional, a planilha pode exigir
importação explícita por vírgula. Não alterar valores para acomodar a abertura.

## Pendências para os três entregáveis obrigatórios

| Entregável | Pendências |
|---|---|
| PDF teórico | Concluído localmente: 30 páginas, requisitos originais confirmados, resultados reais e 13 capturas revisadas. Falta o envio pelo canal acadêmico. |
| Projeto público no GitHub | Atualizar trechos desatualizados do README sobre capturas ausentes e incluir links às imagens e insights; configurar remoto, preparar commit e publicar somente após autorização; conferir acesso público ao link final. |
| Vídeo pitch até quatro minutos | Preparar roteiro, gravar propósito/tecnologias/processamento/demonstração/conclusões, publicar em canal autorizado e conferir acessibilidade do link. Nenhum vídeo/link localizado em docs. |

O repositório local está sem remoto configurado. Não foi verificada a situação
externa do repositório informado anteriormente. A URL local do Streamlit não é
um endereço público de entrega. O enunciado não exige hospedagem pública do
dashboard, mas exige repositório público e link acessível do vídeo.

## Limitações preservadas

Unidade térmica e fuso não confirmados; ausência de identificação de sensores
físicos; médias ponderadas por registros; cobertura de minutos com observações
sem equivalência a disponibilidade comprovada. Comparações horárias não
garantem simultaneidade ou causalidade. Falhas técnicas de ingestão revertem
também o registro da execução, conforme documentado.

O PDF foi gerado em 10/10/2026 mediante autorização. Nesta etapa documental,
nenhum serviço foi iniciado, nenhuma consulta ao banco ou teste de ingestão foi
executado e o CSV preservou seu SHA-256. Não houve alterações no código do pipeline,
commit, push ou publicação. Resultados HTTP e testes anteriores mantêm suas datas;
não comprovam disponibilidade dos serviços após o reinício.
Aguardar autorização antes de qualquer publicação.
