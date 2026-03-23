# =============================
# MATCHING INTERNO (CUADRE DE MONTOS)
# =============================
st.markdown("## 🔍 Conciliación interna por monto")

df_match = df_year.copy()
df_match = df_match[[col_cliente, col_neto, col_fecha]].dropna()

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

        # Si los montos se compensan (ej: 2200 y -2200)
        if abs(row1[col_neto] + row2[col_neto]) < 1:

            matches.append({
                "Cliente 1": row1[col_cliente],
                "Monto 1": row1[col_neto],
                "Cliente 2": row2[col_cliente],
                "Monto 2": row2[col_neto]
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

# =============================
# RESULTADOS
# =============================
df_matches = pd.DataFrame(matches)
df_no_match = pd.DataFrame(no_match)

st.success(f"Se encontraron {len(df_matches)} coincidencias internas")

# =============================
# MOSTRAR MATCHES
# =============================
st.markdown("### ✅ Movimientos que cuadran")
st.dataframe(df_matches, use_container_width=True)

# =============================
# DIFERENCIAS REALES
# =============================
st.markdown("### ❗ Diferencias reales (NO cuadran)")

st.dataframe(df_no_match, use_container_width=True)

# =============================
# DASHBOARD FINAL REAL
# =============================
st.markdown("## 📊 Dashboard Final (REAL)")

total_registros = len(df_match)
total_match = len(df_matches)
total_no_match = len(df_no_match)

monto_no_cuadrado = df_no_match["Monto"].sum() if not df_no_match.empty else 0

col1, col2, col3, col4 = st.columns(4)

col1.metric("Total Registros", total_registros)
col2.metric("Cuadrados", total_match)
col3.metric("No Cuadrados", total_no_match)
col4.metric("Diferencia Real", f"{monto_no_cuadrado:,.2f}")

# =============================
# ALERTA IMPORTANTE
# =============================
if total_no_match > 0:
    st.warning("⚠️ Estos son los montos que realmente debes revisar (no tienen contraparte)")
else:
    st.success("✅ Todo cuadra perfectamente")
