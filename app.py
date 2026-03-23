import streamlit as st
import pandas as pd

st.set_page_config(page_title="Conciliador Anual SISCONT", layout="wide")

# =============================
# TITULO
# =============================
st.title("📊 Conciliador Anual SISCONT")
st.markdown("Analiza el acumulado anual y detecta diferencias por Razón Social")

# =============================
# SUBIR ARCHIVO
# =============================
st.subheader("📂 Subir archivo SISCONT")

file = st.file_uploader("Sube tu Excel SISCONT", type=["xlsx"])

if file:

    df = pd.read_excel(file)

    st.success("Archivo cargado correctamente")

    # =============================
    # LIMPIEZA
    # =============================
    df.columns = df.columns.str.strip()

    # Ajusta nombres según tu archivo
    col_cliente = "Razón Social"
    col_neto = "NETO"
    col_fecha = "Fecha"

    # Convertir fecha
    df[col_fecha] = pd.to_datetime(df[col_fecha], errors="coerce")

    # =============================
    # FILTRO AÑO (opcional)
    # =============================
    st.subheader("📅 Filtrar por año")

    años = df[col_fecha].dt.year.dropna().unique()
    año_seleccionado = st.selectbox("Selecciona año", sorted(años))

    df = df[df[col_fecha].dt.year == año_seleccionado]

    # =============================
    # AGRUPACIÓN
    # =============================
    resumen = df.groupby(col_cliente).agg(
        Total_Neto=("NETO", "sum"),
        Total_Debito=("Débito", "sum"),
        Total_Credito=("Crédito", "sum"),
        Cantidad=("NETO", "count")
    ).reset_index()

    # =============================
    # DIFERENCIA
    # =============================
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
    # TABLA
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
    # SOLO DIFERENCIAS
    # =============================
    st.markdown("## ⚠️ Clientes con diferencias")

    df_diff = resumen[resumen["Diferencia"] != 0]

    st.dataframe(df_diff, use_container_width=True)

    # =============================
    # DESCARGA
    # =============================
    csv = resumen.to_csv(index=False).encode("utf-8")

    st.download_button(
        "📥 Descargar resumen anual",
        csv,
        "resumen_siscont.csv",
        "text/csv"
    )

else:
    st.info("Sube un archivo para comenzar")
