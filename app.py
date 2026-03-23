import streamlit as st
import pandas as pd
import numpy as np
import io

st.set_page_config(page_title="Conciliador Inteligente PRO", layout="wide")

st.title("🧠 Conciliador Inteligente por Razón Social")
st.write("Detecta diferencias y encuentra coincidencias aunque no sean exactas")

# -----------------------------
# SUBIR ARCHIVO
# -----------------------------
archivo = st.file_uploader("📂 Sube tu Excel SISCON", type=["xlsx"])

if archivo:
    df = pd.read_excel(archivo)

    st.subheader("📊 Vista previa")
    st.dataframe(df.head())

    # -----------------------------
    # LIMPIEZA
    # -----------------------------
    df["Fecha"] = pd.to_datetime(df["Fecha"], errors="coerce")
    df["Débito"] = pd.to_numeric(df["Débito"], errors="coerce").fillna(0)
    df["Crédito"] = pd.to_numeric(df["Crédito"], errors="coerce").fillna(0)

    cliente_col = "Razón Social"

    # -----------------------------
    # RESUMEN POR CLIENTE
    # -----------------------------
    resumen = df.groupby(cliente_col).agg({
        "Débito": "sum",
        "Crédito": "sum"
    }).reset_index()

    resumen["Neto"] = resumen["Débito"] - resumen["Crédito"]

    st.subheader("📊 Resumen por cliente")
    st.dataframe(resumen)

    # -----------------------------
    # DIFERENCIAS
    # -----------------------------
    diferencias = resumen[resumen["Neto"].round(2) != 0]

    if not diferencias.empty:
        st.error("🚨 Clientes con diferencias")
        st.dataframe(diferencias)

        # EXPORTAR DIFERENCIAS
        buffer = io.BytesIO()
        diferencias.to_excel(buffer, index=False)
        st.download_button(
            label="📥 Descargar diferencias",
            data=buffer.getvalue(),
            file_name="diferencias_clientes.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        st.success("✅ Todo cuadra por cliente")

    # -----------------------------
    # DETALLE POR CLIENTE
    # -----------------------------
    st.subheader("🔎 Detalle por cliente")

    cliente_select = st.selectbox("Selecciona cliente", df[cliente_col].dropna().unique())

    df_cliente = df[df[cliente_col] == cliente_select]
    st.dataframe(df_cliente.sort_values("Fecha"))

    # -----------------------------
    # MATCHING INTELIGENTE
    # -----------------------------
    st.subheader("🧠 Matching inteligente")

    tolerancia = st.number_input("Tolerancia de monto", value=0.5)
    dias_tolerancia = st.number_input("Tolerancia de días", value=5)

    df["Monto"] = df["Débito"] - df["Crédito"]

    coincidencias = []

    for i in range(len(df)):
        for j in range(i+1, len(df)):
            
            monto1 = df.iloc[i]["Monto"]
            monto2 = df.iloc[j]["Monto"]

            fecha1 = df.iloc[i]["Fecha"]
            fecha2 = df.iloc[j]["Fecha"]

            cliente1 = df.iloc[i][cliente_col]
            cliente2 = df.iloc[j][cliente_col]

            # -----------------------------
            # CONDICIONES DE MATCHING
            # -----------------------------
            mismo_monto = abs(abs(monto1) - abs(monto2)) <= tolerancia
            signo_opuesto = monto1 * monto2 < 0

            fecha_cercana = False
            if pd.notnull(fecha1) and pd.notnull(fecha2):
                fecha_cercana = abs((fecha1 - fecha2).days) <= dias_tolerancia

            if mismo_monto and signo_opuesto:
                score = 0

                if mismo_monto:
                    score += 50
                if signo_opuesto:
                    score += 30
                if fecha_cercana:
                    score += 20

                coincidencias.append({
                    "Monto 1": monto1,
                    "Monto 2": monto2,
                    "Cliente 1": cliente1,
                    "Cliente 2": cliente2,
                    "Fecha 1": fecha1,
                    "Fecha 2": fecha2,
                    "Score (%)": score
                })

    if coincidencias:
        df_match = pd.DataFrame(coincidencias).sort_values(by="Score (%)", ascending=False)

        st.warning("⚠️ Posibles coincidencias encontradas")
        st.dataframe(df_match)

        # EXPORTAR MATCHING
        buffer2 = io.BytesIO()
        df_match.to_excel(buffer2, index=False)

        st.download_button(
            label="📥 Descargar matching",
            data=buffer2.getvalue(),
            file_name="matching_inteligente.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        st.info("No se encontraron coincidencias")
