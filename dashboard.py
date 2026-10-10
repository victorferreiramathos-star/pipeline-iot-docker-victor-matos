"""Dashboard acadêmico de Victor Matos, baseado somente nas views reais."""

import plotly.express as px
import streamlit as st

from src.dashboard_data import filter_frames, indicators, read_views

PAGES = ['Visão geral', 'Temperaturas diárias', 'Cobertura das leituras',
         'Comparação In/Out', 'Qualidade e limitações dos dados']
COLORS = {'In': '#007F86', 'Out': '#C05216'}


@st.cache_data(ttl=60, show_spinner=False)
def cached_views():
    return read_views()


def chart(fig):
    fig.update_layout(template='plotly_white', font=dict(size=14),
                      margin=dict(l=20, r=20, t=65, b=30))
    st.plotly_chart(fig, width='stretch')


def detail_table(frame, filename):
    st.subheader('Dados detalhados do período')
    st.dataframe(frame, width='stretch', hide_index=True)
    st.download_button('Baixar tabela em CSV', frame.to_csv(index=False).encode('utf-8-sig'),
                       file_name=filename, mime='text/csv')


def main():
    st.set_page_config(page_title='IoT Thermal Analytics | Victor Matos', page_icon='📊', layout='wide')
    st.markdown('''<style>
    .stApp {background-color:#F5F7FA;color:#172B3A;}
    [data-testid="stSidebar"] {background-color:#E9EFF3;}
    [data-testid="stMetric"] {background:#FFFFFF;border-top:4px solid #007F86;
      padding:16px;border-radius:8px;color:#172B3A;}
    </style>''', unsafe_allow_html=True)
    st.title('IoT Thermal Analytics | Victor Matos')
    st.caption('Disruptive Architectures: IoT, Big Data e IA · Dados reais · PostgreSQL 16')
    page = st.sidebar.radio('Navegação', PAGES, key='page')
    if st.sidebar.button('Atualizar dados', key='refresh'):
        cached_views.clear()
    try:
        with st.spinner('Consultando as views do PostgreSQL...'):
            frames, fetched_at = cached_views()
    except Exception:
        st.error('Não foi possível consultar o PostgreSQL. Confira o serviço do projeto, o .env local e a existência das três views. Nenhum dado foi alterado.')
        st.stop()
    st.sidebar.caption(f'Consulta em UTC: {fetched_at}. Cache: até 60 segundos; use Atualizar dados para uma nova consulta. UTC refere-se à consulta, não ao horário das observações.')
    if frames['daily'].empty:
        st.info('As views não contêm dados. Execute e valide a ingestão antes de continuar.')
        st.stop()
    dates = st.sidebar.date_input('Período (dias inclusivos)',
                                  value=(frames['daily']['observation_date'].min().date(),
                                         frames['daily']['observation_date'].max().date()), key='period')
    environments = st.sidebar.multiselect('Ambientes', ['In', 'Out'], default=['In', 'Out'], key='environments')
    if len(dates) != 2 or dates[0] > dates[1]:
        st.info('Selecione uma data inicial e uma data final válidas.')
        st.stop()
    selected = filter_frames(frames, dates[0], dates[1], environments)
    daily, coverage, gap = (selected[k] for k in ('daily', 'coverage', 'gap'))
    st.subheader(page)
    metrics = indicators(daily)
    columns = st.columns(4)
    for column, label, value in zip(columns,
        ['Leituras no período', 'Temperatura mínima', 'Temperatura máxima', 'Média ponderada por registros'],
        [f"{metrics['count']:,}".replace(',', '.'),
         '—' if metrics['minimum'] is None else f"{metrics['minimum']:.2f}",
         '—' if metrics['maximum'] is None else f"{metrics['maximum']:.2f}",
         '—' if metrics['mean'] is None else f"{metrics['mean']:.4f}"]):
        column.metric(label, value)
    st.caption('Indicadores respeitam o período e os ambientes selecionados. A média é ponderada pela quantidade de registros, não pelo tempo. Unidade térmica e fuso das observações não confirmados.')
    if page == PAGES[4]:
        st.markdown('''**Interpretação e limites**

- O CSV original possui 97.606 linhas; a ingestão validada preservou 97.605 registros únicos após uma duplicata exata. Esses totais são da auditoria completa, não dos filtros.
- O dataset identifica o local Room Admin e ambientes In/Out; não identifica sensores físicos individuais.
- Cobertura = minutos distintos com registros ÷ 60. Não mede disponibilidade comprovada do sensor. Horas ausentes não são preenchidas.
- Frequências desiguais influenciam médias por registro; múltiplas leituras por minuto não são automaticamente duplicatas.
- Comparações horárias exigem ambos os ambientes; não garantem leituras simultâneas nem causalidade.
- A unidade térmica e o fuso não foram confirmados documentalmente. Não se presume Celsius.
- As linhas dos gráficos conectam apenas observações disponíveis; não representam medições intermediárias.
''')
        st.write('Grupos disponíveis após os filtros:', {'diários': len(daily), 'cobertura': len(coverage), 'comparação': len(gap)})
        st.link_button('Fonte oficial no Kaggle', 'https://www.kaggle.com/datasets/atulanandjha/temperature-readings-iot-devices')
        return
    if daily.empty:
        st.info('Nenhum registro para o período e os ambientes selecionados.')
        return
    labels = {'observation_date': 'Data', 'environment': 'Ambiente', 'avg_temperature': 'Temperatura média (unidade não confirmada)'}
    if page in (PAGES[0], PAGES[1]):
        chart(px.line(daily, x='observation_date', y='avg_temperature', color='environment',
                      color_discrete_map=COLORS, markers=True, labels=labels,
                      title='Evolução diária da temperatura média', hover_data=['reading_count', 'location_name']))
        st.caption('Cada ponto é a média das leituras daquele dia e ambiente. Lacunas não são imputadas.')
    if page == PAGES[0]:
        counts = daily.groupby('environment', as_index=False)['reading_count'].sum()
        chart(px.bar(counts, x='environment', y='reading_count', color='environment',
                     color_discrete_map=COLORS, title='Quantidade de leituras por ambiente',
                     labels={'environment': 'Ambiente', 'reading_count': 'Leituras'}))
        st.caption('Diferenças de volume refletem a amostragem, não a quantidade de sensores.')
        detail_table(daily, 'resumo_diario.csv')
    elif page == PAGES[1]:
        bounds = daily.melt(id_vars=['observation_date', 'environment'],
                            value_vars=['min_temperature', 'max_temperature'],
                            var_name='statistic', value_name='temperature')
        bounds['statistic'] = bounds['statistic'].map({'min_temperature': 'Mínima', 'max_temperature': 'Máxima'})
        chart(px.line(bounds, x='observation_date', y='temperature', color='environment',
                      line_dash='statistic', color_discrete_map=COLORS,
                      title='Temperaturas mínimas e máximas por dia',
                      labels={'temperature': 'Temperatura (unidade não confirmada)', 'observation_date': 'Data', 'statistic': 'Extremo', 'environment': 'Ambiente'}))
        detail_table(daily, 'temperaturas_diarias.csv')
    elif page == PAGES[2]:
        chart(px.scatter(coverage, x='hour_timestamp', y='minute_coverage_pct', color='environment',
                         color_discrete_map=COLORS, title='Cobertura de minutos por hora observada',
                         labels={'hour_timestamp': 'Data e hora (fuso não confirmado)', 'minute_coverage_pct': 'Minutos com registros (%)', 'environment': 'Ambiente'},
                         hover_data=['reading_count', 'observed_minutes', 'additional_readings_in_observed_minutes']))
        st.warning('Cobertura representa minutos com registros, não disponibilidade comprovada do sensor. O denominador é 60 inclusive nas horas parciais das extremidades do período.')
        st.write(f"Grupos com minutos sem registros: {int(coverage['has_unobserved_minutes'].sum())} de {len(coverage)}.")
        detail_table(coverage, 'cobertura_horaria.csv')
    elif page == PAGES[3]:
        st.caption('Comparação exige In e Out selecionados. Diferença = média externa − média interna; positiva indica média externa maior. Médias de cada ambiente são ponderadas por seus registros.')
        st.caption('Os indicadores acima incluem todas as leituras filtradas; o gráfico abaixo inclui somente horas com dados nos dois ambientes.')
        if gap.empty:
            st.info('Nenhuma hora comparável. Selecione ambos os ambientes e um período com leituras nos dois.')
            return
        fig = px.line(gap, x='observation_hour', y='outdoor_minus_indoor',
                      title='Diferença horária entre médias externa e interna',
                      labels={'observation_hour': 'Data e hora (fuso não confirmado)', 'outdoor_minus_indoor': 'Externa − interna (unidade não confirmada)'},
                      hover_data=['indoor_avg_temperature', 'outdoor_avg_temperature', 'indoor_reading_count', 'outdoor_reading_count'])
        fig.add_hline(y=0, line_dash='dash', line_color='#526777')
        chart(fig)
        detail_table(gap, 'comparacao_horaria.csv')


if __name__ == '__main__':
    main()
