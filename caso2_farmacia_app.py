import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


st.set_page_config(page_title='FarmaData Dashboard', page_icon='💊', layout='wide')

st.markdown("""
<style>
    .block-container { padding-top: 1rem; }
    h1 { color: #2e7d32; }
</style>
""", unsafe_allow_html=True)

@st.cache_data
def cargar_datos():
    df = pd.read_csv('caso2_farmacia_dataset.csv')
    df['fecha_venta'] = pd.to_datetime(df['fecha_venta'])
    return df

df = cargar_datos()

with st.sidebar:
    st.header("💊 FarmaData")
    st.markdown("---")
    st.header("🔧 Filtros")

    ciudad_sel = st.multiselect("Ciudad", sorted(df['ciudad'].unique()), default=list(df['ciudad'].unique()))
    categoria_sel = st.multiselect("Categoría", sorted(df['categoria'].unique()), default=list(df['categoria'].unique()))
    regimen_sel = st.multiselect("Régimen", sorted(df['regimen'].unique()), default=list(df['regimen'].unique()))
    formula_sel = st.selectbox("Fórmula médica", ['Todos', 'Sí', 'No'])
    mostrar_criticos = st.checkbox("⚠️ Solo stock crítico (<90 días venc.)")

df_f = df.copy()
if ciudad_sel: df_f = df_f[df_f['ciudad'].isin(ciudad_sel)]
if categoria_sel: df_f = df_f[df_f['categoria'].isin(categoria_sel)]
if regimen_sel: df_f = df_f[df_f['regimen'].isin(regimen_sel)]
if formula_sel != 'Todos': df_f = df_f[df_f['formula_medica'] == formula_sel]
if mostrar_criticos: df_f = df_f[df_f['dias_vencimiento'] < 90]

st.title("💊 FarmaPlus — Dashboard de Ventas y Farmacología")
st.markdown("**Análisis de ventas por medicamento, ciudad y régimen · 2024**")
st.markdown("---")

# KPIs
k1, k2, k3, k4 = st.columns(4)
k1.metric("💰 Ventas Totales", f"${df_f['total_venta_cop'].sum():,.0f}")
k2.metric("📦 Transacciones", f"{len(df_f):,}")
k3.metric("💊 Unidades Vendidas", f"{df_f['cantidad_unidades'].sum():,}")
k4.metric("📊 Ticket Promedio", f"${df_f['total_venta_cop'].mean():,.0f}")

st.markdown("---")

# Tabs para organizar el dashboard
tab1, tab2, tab3 = st.tabs(["📈 Ventas", "💊 Medicamentos", "⚠️ Stock & Alertas"])

with tab1:
    col1, col2 = st.columns([1.5, 1])
    with col1:
        vm = df_f.groupby(df_f['fecha_venta'].dt.to_period('M'))['total_venta_cop'].sum().reset_index()
        vm['fecha_venta'] = vm['fecha_venta'].astype(str)
        fig = px.line(vm, x='fecha_venta', y='total_venta_cop', markers=True,
                      title='📅 Evolución Mensual de Ventas',
                      color_discrete_sequence=['#2e7d32'])
        fig.update_traces(line_width=3)
        fig.update_layout(height=320)
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        vc = df_f.groupby('ciudad')['total_venta_cop'].sum().reset_index()
        fig2 = px.pie(vc, names='ciudad', values='total_venta_cop',
                      title='🏙️ Ventas por Ciudad',
                      color_discrete_sequence=px.colors.qualitative.Set2)
        fig2.update_layout(height=320)
        st.plotly_chart(fig2, use_container_width=True)

    col3, col4 = st.columns([1, 1.5])
    with col3:
        vcat = df_f.groupby('categoria')['total_venta_cop'].sum().reset_index().sort_values('total_venta_cop')
        fig3 = px.bar(vcat, y='categoria', x='total_venta_cop', orientation='h',
                      title='💊 Ventas por Categoría', color='total_venta_cop',
                      color_continuous_scale='Greens', text_auto='.2s')
        fig3.update_layout(height=320, showlegend=False)
        st.plotly_chart(fig3, use_container_width=True)
    with col4:
        pivot = df_f.pivot_table(values='total_venta_cop', index='ciudad',
                                  columns='trimestre', aggfunc='sum').round(0)
        fig4 = px.imshow(pivot, title='🌡️ Ventas por Ciudad y Trimestre',
                          color_continuous_scale='Greens', text_auto=True)
        fig4.update_layout(height=320)
        st.plotly_chart(fig4, use_container_width=True)

with tab2:
    top5 = df_f.groupby('medicamento').agg(
        ventas=('total_venta_cop', 'sum'), unidades=('cantidad_unidades', 'sum')
    ).sort_values('ventas', ascending=False).head(10).reset_index()

    col1, col2 = st.columns(2)
    with col1:
        fig5 = px.bar(top5, y='medicamento', x='ventas', orientation='h',
                      title='🏆 Top 10 Medicamentos por Ventas',
                      color='ventas', color_continuous_scale='Teal', text_auto='.2s')
        fig5.update_layout(height=380, showlegend=False)
        st.plotly_chart(fig5, use_container_width=True)
    with col2:
        fig6 = px.scatter(df_f, x='precio_unitario_cop', y='cantidad_unidades',
                          color='categoria', size='total_venta_cop',
                          hover_data=['medicamento', 'farmacia'],
                          title='💰 Precio vs Cantidad por Categoría')
        fig6.update_layout(height=380)
        st.plotly_chart(fig6, use_container_width=True)

with tab3:
    criticos = df_f[df_f['dias_vencimiento'] < 90].sort_values('dias_vencimiento')
    st.warning(f"⚠️ {len(criticos)} productos con vencimiento en menos de 90 días")
    if len(criticos) > 0:
        cols_show = ['medicamento', 'farmacia', 'ciudad', 'stock_disponible', 'dias_vencimiento', 'proveedor']
        st.dataframe(criticos[cols_show].reset_index(drop=True), use_container_width=True)
        fig7 = px.bar(criticos.groupby('farmacia')['dias_vencimiento'].count().reset_index(),
                      x='farmacia', y='dias_vencimiento',
                      title='⚠️ Productos Críticos por Farmacia',
                      color_discrete_sequence=['#e53935'])
        st.plotly_chart(fig7, use_container_width=True)
    
    st.markdown("---")
    with st.expander("📋 Todos los datos filtrados"):
        st.dataframe(df_f, use_container_width=True)
        st.download_button("⬇️ Descargar CSV", df_f.to_csv(index=False), "farmacia_filtrado.csv")

st.caption("🔧 FarmaData · Streamlit + Plotly | Clase de Visualización de Datos")
