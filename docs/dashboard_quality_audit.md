# Auditoria funcional e pendências visuais — Victor Matos

Data: 08/10/2026. Endereço: http://127.0.0.1:8501.

**Status: validação funcional automatizada aprovada; revisão visual manual pendente.**
Não há ferramenta de navegador local disponível nesta sessão; Playwright e
Selenium não estão instalados. Não foi realizada inspeção visual da interface
renderizada nem captura de tela.

## Checklist

| Item | Evidência e situação |
|---|---|
| Servidor funcionando | Página raiz HTTP 200; saúde HTTP 200 com `ok`. |
| Cinco páginas | Exercitadas por Streamlit AppTest, sem exceções ou mensagens de erro no fluxo normal. |
| Título e Victor Matos | Título correto registrado nos componentes das cinco páginas. |
| Títulos, eixos e legendas | Conferidos nos metadados Plotly; posicionamento e cortes dependem do navegador. |
| Dados reais | Consultas às views com 158, 2.287 e 865 linhas; indicadores comparados com SQL independente. |
| Período/ambiente | Testados filtros, seleção vazia, período sem registros e comparação com somente In. |
| Tabelas e download | Uma tabela e um controle de download nas quatro páginas analíticas. Clique e abertura do arquivo no navegador pendentes. |
| Página de qualidade | Explicações presentes; não exige gráfico, tabela ou download. |
| Mensagens técnicas | Nenhuma exceção exibida nos fluxos exercitados; erro de conexão simulado recebe mensagem segura. Avaliação visual completa pendente. |
| Unidade, fuso, sensores e cobertura | Avisos confirmados no código; não se assume Celsius, fuso ou sensores individuais. |
| Contraste | Razões numéricas das cores de texto configuradas calculadas; aparência final não inspecionada. |
| Referências a outros alunos | Busca em dashboard.py, dashboard_data.py, tema e README não encontrou Felipe/João. Outros projetos não foram acessados; não foi feita comparação externa de originalidade. |
| Capturas reais | Nenhuma capturada; pasta preparada e revisão manual solicitada. |

## Páginas verificadas automaticamente

1. Visão geral: dois gráficos, uma tabela e download.
2. Temperaturas diárias: dois gráficos, uma tabela e download.
3. Cobertura das leituras: um gráfico, uma tabela, download e aviso de cobertura.
4. Comparação In/Out: um gráfico, uma tabela, download e explicação da diferença.
5. Qualidade e limitações dos dados: explicações e identificação do projeto.

Os indicadores globais foram conferidos: 97.605 leituras, mínimo 21, máximo 51
e média ponderada 35,0538599456995. O filtro In de 01/08 a 10/08/2018 retornou
575 leituras, mínimo 27, máximo 30 e média 28,601739130434783.

## Defeito confirmado e corrigido

A função de apresentação sobrescrevia o título de todas as legendas como
`Ambiente`. No gráfico de extremos, os metadados mostravam categorias como
`In, Mínima` e `Out, Máxima`, tornando o cabeçalho incompleto. A sobrescrita foi
removida: o Plotly preserva `Ambiente, Extremo` nesse gráfico.

Correção limitada a `dashboard.py`; adicionado teste de regressão em
`tests/test_dashboard.py`. Não foi uma constatação visual por navegador.

Após a correção: **cinco testes aprovados em 34,252 segundos**, saída 0.
Os avisos ScriptRunContext/cache em memória pertencem ao executor de testes,
não a mensagens mostradas pela aplicação ao usuário.

## Contraste calculado das cores configuradas

| Texto e fundo | Razão calculada |
|---|---:|
| `#172B3A` sobre `#F5F7FA` | 13,56:1 |
| `#172B3A` sobre `#E9EFF3` | 12,55:1 |
| `#172B3A` sobre `#FFFFFF` | 14,55:1 |

Esses cálculos não certificam todos os componentes, estados de foco/hover,
legendas, barras de rolagem ou a aparência renderizada.

## Evidências reais

- `dashboard_audit_http.json`: resposta do servidor e indicação explícita de que não houve inspeção visual.
- `dashboard_audit_tests.txt`: saída dos testes depois da correção.
- `dashboard_components_audit.json`: metadados dos componentes e contraste calculado.
- `screenshots/README.md`: roteiro manual e nomes de cinco capturas numeradas.

## Pendências antes da entrega acadêmica

Solicitada revisão pelo usuário no navegador. Conferir cortes, sobreposições,
contraste efetivo, interação Plotly e download/abertura dos CSVs. Registrar cinco
capturas reais como indicado em `screenshots/README.md`, com responsável e data.
Nenhuma imagem foi fabricada. Não considerar a auditoria visual concluída antes
dessas verificações.

Ingestão, banco, views e CSV não foram modificados. Não foi gerado PDF, commit,
push ou publicação. A documentação final continua aguardando autorização.
