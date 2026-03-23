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
    # MATCHING DETALLE (TU LÓGICA)
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

            if abs(row1[col_neto] + row2[col_neto]) < 1:

                matches.append({
                    "Cliente Origen": row1[col_cliente],
                    "Monto Origen": row1[col_neto],
                    "Fecha Origen": row1[col_fecha],

                    "Cliente Compensa": row2[col_cliente],
                    "Monto Compensa": row2[col_neto],
                    "Fecha Compensa": row2[col_fecha],
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
            })

    df_matches = pd.DataFrame(matches)
    df_no_match = pd.DataFrame(no_match)

    st.dataframe(df_matches, use_container_width=True)

    st.markdown("### ❗ Diferencias reales")
    st.dataframe(df_no_match, use_container_width=True)

    # =============================
    # 🔥 VALIDACIÓN CON ARRASTRE (CLAVE)
    # =============================
    st.markdown("## 🧠 Validación contra acumulado (tipo Excel + arrastre)")

    # incluir año actual + año anterior
    df_validacion = df[
        df[col_fecha].dt.year.isin([año_seleccionado, año_seleccionado - 1])
    ]

    df_grouped = df_validacion.groupby(col_cliente)[col_neto].sum().reset_index()
    df_grouped = df_grouped[df_grouped[col_neto].round(2) != 0]

    evidencia = []

    for _, row in df_grouped.iterrows():
        cliente = row[col_cliente]
        monto = row[col_neto]

        posibles = df_validacion[
            abs(df_validacion[col_neto] + monto) < 1
        ]

        if not posibles.empty:
            for _, p in posibles.iterrows():
                evidencia.append({
                    "Cliente Residual": cliente,
                    "Monto Residual": monto,
                    "Se compensa con": p[col_cliente],
                    "Monto encontrado": p[col_neto],
                    "Fecha": p[col_fecha],
                    "Origen": "Arrastre o movimiento cruzado"
                })
        else:
            evidencia.append({
                "Cliente Residual": cliente,
                "Monto Residual": monto,
                "Se compensa con": "NO ENCONTRADO",
                "Monto encontrado": "",
                "Fecha": "",
                "Origen": "Diferencia real"
            })

    df_evidencia = pd.DataFrame(evidencia)

    st.dataframe(df_evidencia, use_container_width=True)

    # =============================
    # DASHBOARD FINAL
    # =============================
    st.markdown("## 📊 Dashboard Final REAL")

    monto_real = df_grouped[col_neto].sum()

    col1, col2 = st.columns(2)
    col1.metric("Diferencia total (tipo Excel)", f"{monto_real:,.2f}")
    col2.metric("Clientes con residual", len(df_grouped))

else:
    st.info("Sube un archivo para comenzar")
