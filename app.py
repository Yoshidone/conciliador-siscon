import streamlit as st
import pandas as pd
import itertools

st.set_page_config(page_title="Conciliador Anual SISCONT", layout="wide")

# =============================
# TITULO
# =============================
st.title("📊 Conciliador Anual SISCONT")
st.markdown("Análisis + conciliación automática + evidencia real")

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
    # RESUMEN ORIGINAL (NO TOCADO)
    # =============================
    resumen = df_year.groupby(col_cliente).agg(
        Total_Neto=(col_neto, "sum"),
        Total_Debito=(col_debito, "sum"),
        Total_Credito=(col_credito, "sum"),
        Cantidad=(col_neto, "count")
    ).reset_index()

    resumen["Diferencia"] = resumen["Total_Debito"] - resumen["Total_Credito"]

    # =============================
    # DASHBOARD ORIGINAL
    # =============================
    st.markdown("## 📊 Dashboard Anual")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Clientes", resumen.shape[0])
    col2.metric("Total Neto", f"{resumen['Total_Neto'].sum():,.2f}")
    col3.metric("Total Diferencias", f"{resumen['Diferencia'].sum():,.2f}")
    col4.metric("Clientes con diferencia", resumen[resumen["Diferencia"] != 0].shape[0])

    # =============================
    # TABLA ORIGINAL
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
    # MATCHING 1 vs 1
    # =============================
    st.markdown("## 🔍 Conciliación automática (1 vs 1)")

    df_match = df_year[[col_cliente, col_neto, col_fecha]].dropna().copy()
    df_match["usado"] = False

    matches = []
    no_match = []

    tolerancia = 1

    for i, row1 in df_match.iterrows():
        if df_match.loc[i, "usado"]:
            continue

        encontrado = False

        for j, row2 in df_match.iterrows():
            if i == j or df_match.loc[j, "usado"]:
                continue

            if abs(row1[col_neto] + row2[col_neto]) <= tolerancia:

                matches.append({
                    "Cliente 1": row1[col_cliente],
                    "Monto 1": row1[col_neto],
                    "Fecha 1": row1[col_fecha],

                    "Cliente 2": row2[col_cliente],
                    "Monto 2": row2[col_neto],
                    "Fecha 2": row2[col_fecha],
                })

                df_match.loc[i, "usado"] = True
                df_match.loc[j, "usado"] = True
                encontrado = True
                break

        if not encontrado:
            no_match.append({
                "Cliente": row1[col_cliente],
                "Monto": row1[col_neto],
                "Fecha": row1[col_fecha]
            })

    df_matches = pd.DataFrame(matches)
    df_no_match = pd.DataFrame(no_match)

    st.dataframe(df_matches, use_container_width=True)

    # =============================
    # MATCHING AVANZADO (2 vs 1)
    # =============================
    st.markdown("## 🧠 Conciliación avanzada (2 vs 1)")

    group_matches = []

    for comb in itertools.combinations(range(len(df_no_match)), 3):

        i, j, k = comb

        a = df_no_match.iloc[i]
        b = df_no_match.iloc[j]
        c = df_no_match.iloc[k]

        if abs(a["Monto"] + b["Monto"] + c["Monto"]) <= tolerancia:

            group_matches.append({
                "Cliente 1": a["Cliente"],
                "Monto 1": a["Monto"],

                "Cliente 2": b["Cliente"],
                "Monto 2": b["Monto"],

                "Cliente 3": c["Cliente"],
                "Monto 3": c["Monto"],
            })

    df_group = pd.DataFrame(group_matches)

    st.dataframe(df_group, use_container_width=True)

    # =============================
    # DIFERENCIA REAL FINAL
    # =============================
    usados_grupo = set()

    for match in group_matches:
        usados_grupo.update([
            match["Monto 1"],
            match["Monto 2"],
            match["Monto 3"]
        ])

    df_final = df_no_match[~df_no_match["Monto"].isin(usados_grupo)]

    st.markdown("## ❗ Diferencias reales finales")
    st.dataframe(df_final, use_container_width=True)

    # =============================
    # DASHBOARD FINAL REAL
    # =============================
    st.markdown("## 📊 Dashboard Final REAL")

    total = len(df_match)
    conciliados = len(df_matches) + len(df_group)
    pendientes = len(df_final)
    monto_real = df_final["Monto"].sum() if not df_final.empty else 0

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total registros", total)
    col2.metric("Conciliados", conciliados)
    col3.metric("Pendientes reales", pendientes)
    col4.metric("Diferencia real", f"{monto_real:,.2f}")

else:
    st.info("Sube un archivo para comenzar")
