col1, col2 = st.columns(2)

        fpsi = col1.number_input("Fact PSI", key=mes+"vfp")
        lpsi = col2.number_input("Lab PSI", key=mes+"vlp")

        var = max((fpsi - lpsi - 3730),0)*0.3
        bruto = var + 741

        retenido = bruto * 0.30
        neto = bruto * 0.70

        total_ingresos += bruto
        total_retenido += retenido
        netos.append(neto)

        st.write(f"Neto: {round(neto,2)} €")

# ---------------- IRPF REAL ----------------
def calcular_irpf(base):
    impuesto = 0

    tramos = [
        (12450, 0.19),
        (20200, 0.24),
        (35200, 0.30),
        (60000, 0.37),
        (300000, 0.45)
    ]

    anterior = 0

    for limite, tipo in tramos:
        if base > limite:
            impuesto += (limite - anterior) * tipo
            anterior = limite
        else:
            impuesto += (base - anterior) * tipo
            return impuesto

    impuesto += (base - anterior) * 0.47
    return impuesto

irpf_real = calcular_irpf(total_ingresos)

# ---------------- RESULTADOS ----------------
st.header("📊 RESUMEN HACIENDA")

col1, col2, col3 = st.columns(3)

col1.metric("Ingresos", f"{round(total_ingresos,2)} €")
col2.metric("Retenido (30%)", f"{round(total_retenido,2)} €")
col3.metric("IRPF real", f"{round(irpf_real,2)} €")

diferencia = total_retenido - irpf_real

if diferencia > 0:
    st.success(f"🟢 Hacienda te devolverá aprox: {round(diferencia,2)} €")
else:
    st.error(f"🔴 Te faltará pagar aprox: {round(abs(diferencia),2)} €")

# ---------------- GRAFICA ----------------
st.header("📈 Evolución")

df = pd.DataFrame({
    "Mes": meses*2,
    "Neto": netos
