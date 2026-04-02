import streamlit as st
import pandas as pd

st.set_page_config(page_title="Nivel Dios TOTAL", layout="wide")

st.title("💰 Facturación + IRPF Inteligente")

meses = ["Enero","Febrero","Marzo","Abril","Mayo","Junio",
         "Julio","Agosto","Septiembre","Octubre","Noviembre","Diciembre"]

total_ingresos = 0
total_retenido = 0

netos_mensuales = []
brutos_mensuales = []

# ---------------- COLMENAR ----------------
st.header("🏥 COLMENAR")

for mes in meses:
    with st.expander(mes):

        col1, col2, col3, col4 = st.columns(4)

        fg = col1.number_input("Fact General", key=mes+"fg")
        lg = col2.number_input("Lab General", key=mes+"lg")
        fpsi = col3.number_input("Fact PSI", key=mes+"fp")
        lpsi = col4.number_input("Lab PSI", key=mes+"lp")

        fijo_comp = 708.21
        var_comp = max(0,(fg - 1532 - lg)*0.35 + (fpsi - 1558.18 - lpsi)*0.3)
        bruto_comp = fijo_comp + var_comp

        fijo_anexo = 800
        var_anexo = max(0,(fg - 1404.33 - lg)*0.35 + (fpsi - 1428.33 - lpsi)*0.3)
        bruto_anexo = fijo_anexo + var_anexo

        bruto = max(bruto_comp, bruto_anexo)

        retenido = bruto * 0.30
        neto = bruto * 0.70

        total_ingresos += bruto
        total_retenido += retenido

        brutos_mensuales.append(bruto)
        netos_mensuales.append(neto)

        st.write(f"Neto: {round(neto,2)} €")

# ---------------- VALDEMORO ----------------
st.header("🏥 VALDEMORO")

for mes in meses:
    with st.expander(mes):

        col1, col2 = st.columns(2)

        fpsi = col1.number_input("Fact PSI", key=mes+"vfp")
        lpsi = col2.number_input("Lab PSI", key=mes+"vlp")

        var = max((fpsi - lpsi - 3730),0)*0.3
        bruto = var + 741

        retenido = bruto * 0.30
        neto = bruto * 0.70

        total_ingresos += bruto
        total_retenido += retenido

        brutos_mensuales.append(bruto)
        netos_mensuales.append(neto)

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
st.header("📊 HACIENDA")

col1, col2, col3 = st.columns(3)

col1.metric("Ingresos", f"{round(total_ingresos,2)} €")
col2.metric("Retenido", f"{round(total_retenido,2)} €")
col3.metric("IRPF real", f"{round(irpf_real,2)} €")

diferencia = total_retenido - irpf_real

# ---------------- ALERTA ----------------
if diferencia > 0:
    st.success(f"🟢 Te devolverán aprox: {round(diferencia,2)} €")
    ajuste = (irpf_real / total_ingresos) * 100
    st.info(f"💡 Podrías bajar retención a ~{round(ajuste,1)}%")
else:
    falta = abs(diferencia)
    st.error(f"🔴 Te faltará pagar aprox: {round(falta,2)} €")
    ajuste = (irpf_real / total_ingresos) * 100
    st.warning(f"⚠️ Deberías subir retención a ~{round(ajuste,1)}%")

# ---------------- GRAFICAS ----------------
st.header("📈 Evolución mensual")

df = pd.DataFrame({
    "Mes": meses*2,
    "Bruto": brutos_mensuales
})

st.line_chart(df["Bruto"])

# ---------------- PREDICCION ----------------
st.header("🔮 Predicción anual")

meses_con_datos = len([x for x in brutos_mensuales if x > 0])

if meses_con_datos > 0:
    media = total_ingresos / meses_con_datos
    prediccion = media * 12
    irpf_pred = calcular_irpf(prediccion)

    st.write(f"📊 Ingreso estimado: {round(prediccion,2)} €")
    st.write(f"💸 IRPF estimado anual: {round(irpf_pred,2)} €")
