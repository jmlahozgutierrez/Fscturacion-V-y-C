import streamlit as st

st.set_page_config(page_title="Facturación clínica", layout="wide")

st.title("💰 App Facturación Clínica")

# Configuración
st.sidebar.header("Configuración")
irpf = st.sidebar.number_input("IRPF Colmenar (%)", value=30)
retencion_val = st.sidebar.number_input("Retención Valdemoro (%)", value=25)
fijo_val = st.sidebar.number_input("Fijo Valdemoro (€)", value=741)

meses = ["Enero","Febrero","Marzo","Abril","Mayo","Junio","Julio","Agosto","Septiembre","Octubre","Noviembre","Diciembre"]

st.header("📊 Introducir datos")

datos = []

for mes in meses:
    st.subheader(mes)

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        fact_general = st.number_input(f"{mes} Fact General", key=mes+"fg")
    with col2:
        lab_general = st.number_input(f"{mes} Lab General", key=mes+"lg")
    with col3:
        fact_psi = st.number_input(f"{mes} Fact PSI", key=mes+"fp")
    with col4:
        lab_psi = st.number_input(f"{mes} Lab PSI", key=mes+"lp")

    # Colmenar cálculo
    fijo_comp = 708.21
    var_comp = max(0,(fact_general - 1532 - lab_general)*0.35 + (fact_psi - 1558.18 - lab_psi)*0.3)
    bruto_comp = fijo_comp + var_comp

    fijo_anexo = 800
    var_anexo = max(0,(fact_general - 1404.33 - lab_general)*0.35 + (fact_psi - 1428.33 - lab_psi)*0.3)
    bruto_anexo = fijo_anexo + var_anexo

    bruto_final = max(bruto_comp, bruto_anexo)
    neto_col = bruto_final * (1 - irpf/100)

    # Valdemoro cálculo
    var_val = max((fact_psi - lab_psi - 3730),0)*0.3
    bruto_val = var_val + fijo_val
    neto_val = bruto_val * (1 - retencion_val/100)

    total = neto_col + neto_val

    datos.append(total)

    st.write(f"💵 Neto total {mes}: {round(total,2)} €")

st.header("📈 Resumen anual")

st.write(f"Total anual estimado: {round(sum(datos),2)} €")
