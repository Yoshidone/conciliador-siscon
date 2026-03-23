# =============================
# 🔍 MATCHING INTERNO (SIN CAMBIAR TU LÓGICA)
# =============================
st.markdown("## 🔍 Conciliación interna por monto (evidencia)")

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

        # si se compensan
        if abs(row1[col_neto] + row2[col_neto]) < 1:

            matches.append({
                "Cliente 1": row1[col_cliente],
                "Monto 1": row1[col_neto],
                "Fecha 1": row1[col_fecha],

                "Cliente 2": row2[col_cliente],
                "Monto 2": row2[col_neto],
                "Fecha 2": row2[col_fecha],

                "Evidencia": "Compensación encontrada"
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

# =============================
# RESULTADOS
# =============================
st.markdown("### ✅ Movimientos que se compensan")
st.dataframe(df_matches, use_container_width=True)

st.markdown("### ❗ Diferencias reales (sin compensación)")
st.dataframe(df_no_match, use_container_width=True)

# =============================
# DASHBOARD FINAL REAL
# =============================
st.markdown("## 📊 Dashboard Final (real)")

total = len(df_match)
conciliados = len(df_matches)
pendientes = len(df_no_match)

monto_real = df_no_match["Monto"].sum() if not df_no_match.empty else 0

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total registros", total)
col2.metric("Conciliados", conciliados)
col3.metric("Pendientes", pendientes)
col4.metric("Diferencia real", f"{monto_real:,.2f}")

# =============================
# MENSAJE CLAVE
# =============================
if monto_real != 0:
    st.warning("⚠️ Esta es la diferencia REAL que no tiene compensación en el archivo")
else:
    st.success("✅ Todo está conciliado correctamente")
