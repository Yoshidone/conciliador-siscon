import streamlit as st
import pandas as pd

st.set_page_config(page_title="Conciliador Anual SISCONT", layout="wide")

# =============================
# TITULO
# =============================
st.title("📊 Conciliador Anual SISCONT")
st.markdown("Analiza el acumulado anual y detecta diferencias reales por Razón Social")

# =============================
# SUBIR ARCHIVO
# =============================
st.subheader("📂 Subir archivo SISCONT")

file = st.file_uploader("Sube tu Excel SISCONT", type=["xlsx"])

if file:

    df = pd.read_excel(file)
    df.columns = df.columns.str.strip()

    st.success("Archivo cargado correctamente")

    # =============================
    # COLUMNAS
    # =============================
    col_cliente = "Razón Social"
    col_neto = "NETO"
    col_fecha = "Fecha"
    col_debito = "Débito"
    col_credito = "Crédito"

    # =============================
    # LIMPIEZA
    # =============================
    df[col_fecha] = pd.to_datetime(df[col_fecha], errors="coerce")

    # =============================
    # FILTRO AÑO
    # =============================
    st.subheader("📅 Filtrar por año")

    años = df[col_fecha].dt.year.dropna().unique()
    año_seleccionado = st.selectbox("Selecciona año", sorted(años))

    df_year = df[df[col_fecha].dt.year == año_seleccionado]

    # =============================
    # AGRUPACIÓN
    # =============================
    resumen = df_year.groupby(col_cliente).agg(
        Total_Neto=(col_neto, "sum"),
        Total_Debito=(col_debito, "sum"),
        Total_Credito=(col_credito, "sum"),
        Cantidad=(col_neto, "count")
    ).reset_index()

    resumen["Diferencia"] = resumen["Total_Debito"] - resumen["Total_Credito"]

    # =============================
    # DASHBOARD
    # =============================
    total_clientes = resumen.shape[0]
    total_neto = resumen["Total_Neto"].sum()
    total_diferencia = resumen["Diferencia"].sum()
    clientes_con_diferencia = resumen[resumen["Diferencia"] != 0].shape[0]

    st.markdown("## 📊 Dashboard Anual")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Clientes", total_clientes)
    col2.metric("Total Neto", f"{total_neto:,.2f}")
    col3.metric("Total Diferencias", f"{total_diferencia:,.2f}")
    col4.metric("Clientes con diferencia", clientes_con_diferencia)

    # =============================
    # TABLA PRINCIPAL
    # =============================
    st.markdown("## 📋 Detalle por Cliente")

    st.dataframe(
        resumen.style.applymap(
            lambda x: "background-color: red" if x != 0 else "",
            subset=["Diferencia"]
        ),
        use_container_width=True
    )

    # =============================
    # AJUSTE 2024 → 2025
    # =============================
    st.markdown("## 🔄 Ajuste por arrastre (año anterior)")

    df_prev = df[df[col_fecha].dt.year == (año_seleccionado - 1)]
    df_dic = df_prev[df_prev[col_fecha].dt.month == 12]

    if not df_dic.empty:

        ajuste = df_dic.groupby(col_cliente).agg(
            Ajuste_Anterior=(col_neto, "sum")
        ).reset_index()

        resumen_ajustado = resumen.merge(ajuste, on=col_cliente, how="left")
        resumen_ajustado["Ajuste_Anterior"] = resumen_ajustado["Ajuste_Anterior"].fillna(0)

        resumen_ajustado["Diferencia_Ajustada"] = (
            resumen_ajustado["Diferencia"] + resumen_ajustado["Ajuste_Anterior"]
        )

        st.info("Incluye movimientos de diciembre del año anterior")

        st.dataframe(
            resumen_ajustado.style.applymap(
                lambda x: "background-color: orange" if x != 0 else "",
                subset=["Diferencia_Ajustada"]
            ),
            use_container_width=True
        )

        # =============================
        # DASHBOARD AJUSTADO
        # =============================
        st.markdown("## 📊 Dashboard Ajustado")

        total_dif_ajustada = resumen_ajustado["Diferencia_Ajustada"].sum()
        clientes_ajustados = resumen_ajustado[
            resumen_ajustado["Diferencia_Ajustada"] != 0
        ].shape[0]

        col1, col2 = st.columns(2)
        col1.metric("Total Diferencia Ajustada", f"{total_dif_ajustada:,.2f}")
        col2.metric("Clientes con diferencia ajustada", clientes_ajustados)

    else:
        st.warning("No hay datos de diciembre del año anterior")

    # =============================
    # DESCARGA
    # =============================
    csv = resumen.to_csv(index=False).encode("utf-8")

    st.download_button(
        "📥 Descargar resumen",
        csv,
        "resumen_siscont.csv",
        "text/csv"
    )

else:
    st.info("Sube un archivo para comenzar")
