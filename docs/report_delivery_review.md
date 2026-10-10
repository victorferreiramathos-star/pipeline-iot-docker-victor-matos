# Revisão do relatório acadêmico — Victor Matos

Data: 10/10/2026, America/Sao_Paulo.

## Resultado

O [PDF final](relatorio_final_victor_matos.pdf) tem 30 páginas: 17 páginas de
conteúdo e 13 páginas de figuras reais em paisagem. O relatório contém arquitetura,
ambiente, Docker, PostgreSQL, ingestão, staging, auditoria, reconciliação, as três
views, dashboard, testes, resultados, insights, uso prático, limitações e referências.
O apêndice reproduz o SQL implementado sem executá-lo.

## Requisitos originais

O PDF acadêmico original foi localizado em Downloads, relido nas sete páginas
e preservado como [orientacao_academica_original.pdf](orientacao_academica_original.pdf).
Seu SHA-256 corresponde ao arquivo de origem. A página 6 exige contextualização,
passos realizados, explicação detalhada de três views, prints das visualizações
e insights com sugestões de uso prático. Todos estão presentes. Não há exigência
expressa de formato ABNT ou número de páginas no enunciado fornecido.

## Verificações realizadas

- [x] Pasta correta e arquivos de código/evidência presentes.
- [x] Cinco PNGs principais presentes; treze imagens incorporadas no total.
- [x] Resultados armazenados das dezesseis verificações CSV conferidos.
- [x] Saída dos nove testes anteriores conferida; nenhuma reexecução alegada.
- [x] PDF aberto e todas as 30 páginas renderizadas sem erro.
- [x] Todas as páginas examinadas visualmente em oito folhas de revisão.
- [x] Páginas 11, 16, 27 e 30 também examinadas individualmente em maior resolução.
- [x] Tabelas, paginação, acentos, SQL e proporções das imagens conferidos.
- [x] Nenhuma página vazia ou texto fora dos limites da página.
- [x] Pixels RGB de todas as 13 imagens incorporadas iguais aos PNGs de origem.
- [x] Cinco capturas principais correspondem às cinco páginas do dashboard.
- [x] Avisos de unidade, fuso, sensores, cobertura e médias preservados.
- [x] Pendência do teste manual dos quatro downloads explicitada na página 11.
- [x] CSV original manteve SHA-256 esperado.

As capturas principais possuem limites e cortes da tela original; as
complementares mostram os gráficos e avisos restantes. Não foram editadas,
montadas ou sintetizadas. O PDF mantém a proporção e todos os pixels das imagens,
com redimensionamento de apresentação, sem recorte adicional.

Dados técnicos e hashes estão em [pdf_review_validation.json](pdf_review_validation.json).
As renderizações reais do PDF estão em `pdf_review/`; não são novas capturas do
dashboard e não substituem os PNGs de `screenshots/`.

## Escopo preservado e pendências

Docker e Streamlit não foram iniciados; o banco não foi acessado ou modificado.
Código de ingestão, views, dashboard e CSV não foram alterados. Nenhum commit,
push ou publicação foi realizado. ReportLab e PyMuPDF foram instalados somente
no ambiente virtual para leitura, geração e inspeção documental; requirements.txt
do pipeline não foi alterado.

Ainda falta conferir os downloads manualmente no navegador, atualizar os trechos
desatualizados do README sobre ausência de capturas e incluir os links às imagens,
publicar o repositório mediante autorização e preparar o vídeo de até quatro
minutos com link acessível. O PDF está concluído localmente; o envio acadêmico
ainda depende do usuário. Nenhum link público foi declarado validado.
