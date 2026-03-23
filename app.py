import streamlit as st
import pandas as pd

st.set_page_config(page_title="Conciliador Anual SISCONT", layout="wide")

# =============================
# TITULO
# =============================
st.title("📊 Conciliador Anual SISCONT")
st.markdown("Análisis + conciliación automática + evidencia de compensaciones")

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

    df[col_fecha] = pd.to_datetime(df[col_fecha], errors="coerce")

    # =============================
    # FILTRO AÑO
    # =============================
    st.subheader("📅 Filtrar por año")

    años = df[col_fecha].dt.year.dropna().unique()
    año_seleccionado = st.selectbox("Selecciona año", sorted(años))

    df_year = df[df[col_fecha].dt.year == año_seleccionado]

    # =============================
    # RESUMEN CONTABLE
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
    st.markdown("## 📊 Dashboard Anual")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Clientes", resumen.shape[0])
    col2.metric("Total Neto", f"{resumen['Total_Neto'].sum():,.2f}")
    col3.metric("Total Diferencias", f"{resumen['Diferencia'].sum():,.2f}")
    col4.metric("Clientes con diferencia", resumen[resumen["Diferencia"] != 0].shape[0])

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
    # MATCHING INTERNO (CON EVIDENCIA)
    # =============================
    st.markdown("## 🔍 Conciliación automática con evidencia")

    df_match = df_year[[col_cliente, col_neto, col_fecha]].dropna().copy()
    df_match["usado"] = False

    matches = []
    no_match = []

    for i, row1 in df_match.iterrows():
        if df_match.loc[i, "usado"]:
            continue

        encontrado = False

        for j, row2 in df_match.iterrows():
            if i == j or df_match.loc[j, "usado"]:
                continue

            # condición de compensación
            if abs(row1[col_neto] + row2[col_neto]) < 1:

                matches.append({
                    "Cliente Origen": row1[col_cliente],
                    "Monto Origen": row1[col_neto],
                    "Fecha Origen": row1[col_fecha],

                    "Cliente Compensa": row2[col_cliente],
                    "Monto Compensa": row2[col_neto],
                    "Fecha Compensa": row2[col_fecha],

                    "Comentario": "Compensación detectada automáticamente"
                })

                df_match.loc[i, "usado"] = True
                df_match.loc[j, "usado"] = True
                encontrado = True
                break

        if not encontrado:
            no_match.append({
                "Cliente": row1[col_cliente],
                "Monto": row1[col_neto],
                "Fecha": row1[col_fecha],
                "Estado": "Sin compensación"
            })

    df_matches = pd.DataFrame(matches)
    df_no_match = pd.DataFrame(no_match)

    # =============================
    # MOSTRAR MATCHES (EVIDENCIA)
    # =============================
    st.markdown("### ✅ Evidencia de compensaciones")

    st.dataframe(df_matches, use_container_width=True)

    # =============================
    # DIFERENCIAS REALES
    # =============================
    st.markdown("### ❗ Diferencias reales")

    st.dataframe(df_no_match, use_container_width=True)

    # =============================
    # DASHBOARD FINAL REAL
    # =============================
    st.markdown("## 📊 Dashboard Final REAL")

    total = len(df_match)
    conciliados = len(df_matches)
    pendientes = len(df_no_match)

    monto_real = df_no_match["Monto"].sum() if not df_no_match.empty else 0

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Registros", total)
    col2.metric("Conciliados", conciliados)
    col3.metric("Pendientes", pendientes)
    col4.metric("Diferencia Real", f"{monto_real:,.2f}")

    # =============================
    # DESCARGAS
    # =============================
    st.download_button(
        "📥 Descargar evidencia",
        df_matches.to_csv(index=False).encode("utf-8"),
        "evidencia_matching.csv",
        "text/csv"
    )

    st.download_button(
        "📥 Descargar diferencias reales",
        df_no_match.to_csv(index=False).encode("utf-8"),
        "diferencias_reales.csv",
        "text/csv"
    )

else:
    st.info("Sube un archivo para comenzar")
