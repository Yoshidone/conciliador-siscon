import streamlit as st
import pandas as pd

st.set_page_config(page_title="Conciliador Financiero Inteligente", layout="wide")

# =============================
# TITULO
# =============================
st.title("📊 Conciliador Financiero Inteligente")
st.markdown("Detecta diferencias y encuentra coincidencias aunque no sean exactas")

# =============================
# SUBIR ARCHIVOS
# =============================
st.subheader("📂 Subir archivos")

file1 = st.file_uploader("Archivo 1", type=["xlsx"])
file2 = st.file_uploader("Archivo 2", type=["xlsx"])

if file1 and file2:

    df1 = pd.read_excel(file1)
    df2 = pd.read_excel(file2)

    st.success("Archivos cargados correctamente")

    # =============================
    # CONFIGURACIÓN
    # =============================
    st.subheader("🧠 Matching inteligente")

    tolerancia_monto = st.number_input("Tolerancia de monto", value=0.5)
    tolerancia_dias = st.number_input("Tolerancia de días", value=4)

    # =============================
    # LIMPIEZA
    # =============================
    df1.columns = df1.columns.str.strip()
    df2.columns = df2.columns.str.strip()

    # Ajusta estos nombres según tu archivo
    col_cliente = "Razón Social"
    col_monto = "NETO"
    col_fecha = "Fecha"

    df1[col_fecha] = pd.to_datetime(df1[col_fecha], errors="coerce")
    df2[col_fecha] = pd.to_datetime(df2[col_fecha], errors="coerce")

    df2["usado"] = False

    matches = []

    # =============================
    # MATCHING 1 A 1
    # =============================
    for i, row1 in df1.iterrows():
        for j, row2 in df2.iterrows():

            if df2.loc[j, "usado"]:
                continue

            # filtro por cliente
            if str(row1[col_cliente]).strip().lower() != str(row2[col_cliente]).strip().lower():
                continue

            # diferencia monto
            diff_monto = abs(row1[col_monto] - row2[col_monto])

            # diferencia fechas
            diff_fecha = abs((row1[col_fecha] - row2[col_fecha]).days)

            if diff_monto <= tolerancia_monto and diff_fecha <= tolerancia_dias:

                score = 100 - (diff_monto * 10 + diff_fecha * 2)

                matches.append({
                    "Monto 1": row1[col_monto],
                    "Monto 2": row2[col_monto],
                    "Cliente": row1[col_cliente],
                    "Fecha 1": row1[col_fecha],
                    "Fecha 2": row2[col_fecha],
                    "Diferencia": row1[col_monto] - row2[col_monto],
                    "Score (%)": max(score, 0)
                })

                df2.loc[j, "usado"] = True
                break

    df_resultado = pd.DataFrame(matches)

    # =============================
    # DASHBOARD
    # =============================
    if not df_resultado.empty:

        total_registros = len(df_resultado)
        total_diferencias = len(df_resultado[df_resultado["Diferencia"] != 0])
        monto_total_diferencia = df_resultado["Diferencia"].sum()
        porcentaje_diferencia = (total_diferencias / total_registros) * 100

        st.markdown("## 📊 Dashboard de Diferencias")

        col1, col2, col3, col4 = st.columns(4)

        col1.metric("Total Matching", total_registros)
        col2.metric("Con Diferencias", total_diferencias)
        col3.metric("Monto Total Dif", f"{monto_total_diferencia:,.2f}")
        col4.metric("% Diferencias", f"{porcentaje_diferencia:.2f}%")

        st.warning("⚠️ Posibles coincidencias encontradas")

        # =============================
        # TABLA
        # =============================
        st.dataframe(
            df_resultado.style.applymap(
                lambda x: "background-color: red" if x != 0 else "",
                subset=["Diferencia"]
            ),
            use_container_width=True
        )

        # =============================
        # DESCARGA
        # =============================
        csv = df_resultado.to_csv(index=False).encode("utf-8")

        st.download_button(
            "📥 Descargar matching",
            csv,
            "matching_resultado.csv",
            "text/csv"
        )

    else:
        st.error("No se encontraron coincidencias")
