import streamlit as st
import pandas as pd
from itertools import combinations

st.set_page_config(page_title="Conciliador Anual SISCONT", layout="wide")

# =============================
# TITULO
# =============================
st.title("📊 Conciliador Anual SISCONT - Modo Auditor")

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
        Cantidad=(col_neto, "count")
    ).reset_index()

    resumen["Diferencia"] = resumen["Total_Neto"]

    # =============================
    # DASHBOARD
    # =============================
    st.markdown("## 📊 Dashboard")

    col1, col2, col3 = st.columns(3)
    col1.metric("Clientes", resumen.shape[0])
    col2.metric("Total Neto", f"{resumen['Total_Neto'].sum():,.2f}")
    col3.metric("Clientes con diferencia", resumen[abs(resumen["Diferencia"]) > 1].shape[0])

    # =============================
    # TABLA
    # =============================
    st.markdown("## 📋 Detalle por Cliente")

    st.dataframe(
        resumen.style.applymap(
            lambda x: "background-color: red" if abs(x) > 1 else "",
            subset=["Diferencia"]
        ),
        use_container_width=True
    )

    # =============================
    # 🔍 MATCHING INTELIGENTE
    # =============================
    st.markdown("## 🔍 Compensaciones detectadas")

    df_match = df_year[[col_cliente, col_neto, col_fecha]].dropna().copy()
    df_match["usado"] = False

    valores = df_match.reset_index()
    matches = []

    # -------- 1 vs 1 --------
    for i, row1 in valores.iterrows():
        if valores.loc[i, "usado"]:
            continue

        for j, row2 in valores.iterrows():
            if i == j or valores.loc[j, "usado"]:
                continue

            if abs(row1[col_neto] + row2[col_neto]) < 1:

                matches.append({
                    "Tipo": "1 vs 1",
                    "Detalle": f"{row1[col_cliente]} ({row1[col_neto]}) + {row2[col_cliente]} ({row2[col_neto]})"
                })

                valores.loc[i, "usado"] = True
                valores.loc[j, "usado"] = True
                break

    # -------- combinaciones --------
    no_usados = valores[valores["usado"] == False]

    for i, row_neg in no_usados.iterrows():

        if valores.loc[i, "usado"]:
            continue

        if row_neg[col_neto] >= 0:
            continue

        positivos = valores[
            (valores["usado"] == False) &
            (valores[col_neto] > 0)
        ]

        lista_valores = list(positivos.index)
        encontrado = False

        for r in range(2, 4):
            for combo in combinations(lista_valores, r):

                suma = sum(valores.loc[k, col_neto] for k in combo)

                if abs(suma + row_neg[col_neto]) < 1:

                    detalle = " + ".join(
                        [f"{valores.loc[k, col_cliente]} ({valores.loc[k, col_neto]})" for k in combo]
                    )

                    matches.append({
                        "Tipo": f"{r} vs 1",
                        "Detalle": f"{detalle} = {row_neg[col_neto]}"
                    })

                    for k in combo:
                        valores.loc[k, "usado"] = True

                    valores.loc[i, "usado"] = True
                    encontrado = True
                    break

            if encontrado:
                break

    df_matches = pd.DataFrame(matches)

    if not df_matches.empty:
        st.success("✅ Se encontraron compensaciones")
        st.dataframe(df_matches, use_container_width=True)
    else:
        st.warning("No se encontraron compensaciones")

    # =============================
    # ❗ NO CUADRA
    # =============================
    st.markdown("## ❗ Movimientos que NO cuadran")

    df_no_cuadra = valores[valores["usado"] == False]

    if not df_no_cuadra.empty:

        st.dataframe(
            df_no_cuadra[[col_cliente, col_neto, col_fecha]],
            use_container_width=True
        )

        monto_no_cuadra = df_no_cuadra[col_neto].sum()

        st.error(f"🚨 Diferencia sin compensar: {monto_no_cuadra:,.2f}")

    else:
        st.success("🎯 Todo cuadra perfectamente")

    # =============================
    # DESCARGA
    # =============================
    csv = resumen.to_csv(index=False).encode("utf-8")

    st.download_button(
        "📥 Descargar resumen",
        csv,
        "resumen.csv",
        "text/csv"
    )

else:
    st.info("Sube un archivo para comenzar")
