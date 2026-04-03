import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials

st.set_page_config(page_title="Facturación PRO", layout="wide")

st.title("💰 Facturación Clínica PRO")

# ---------------- CONEXIÓN GOOGLE SHEETS ----------------
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

creds_dict = dict(st.secrets["gcp_service_account"])

creds = ServiceAccountCredentials.from_json_keyfile_dict(
    creds_dict, scope
)

client = gspread.authorize(creds)

sheet = client.open_by_url("https://docs.google.com/spreadsheets/d/1JgpD7qiclpmTuLoHDWCIWdtJ5DPdZKeURFwkXv3_e7U/edit").sheet1

# ---------------- VARIABLES ----------------
meses = ["Enero","Febrero","Marzo","Abril","Mayo","Junio",
         "Julio","Agosto","Septiembre","Octubre","Noviembre","Diciembre"]

total_ingresos = 0
total_retenido = 0
netos = []

datos_guardar = []

# ---------------- LOOP ----------------
for mes in meses:

    st.header(f"📅 {mes}")

    col1, col2 = st.columns(2)

    # -------- COLMENAR --------
    with col1:
        st.subheader("🏥 Colmenar")

        fg = st.number_input("Fact General", key=mes+"fg")
        lg = st.number_input("Lab General", key=mes+"lg")
        fpsi = st.number_input("Fact PSI", key=mes+"fpsi")
        lpsi = st.number_input("Lab PSI", key=mes+"lpsi")

        fijo = 800
        variable = max(0,(fg - 1404.33 - lg)*0.35 + (fpsi - 1428.33 - lpsi)*0.3)

        bruto_col = fijo + variable
        neto_col = bruto_col * 0.70

    # -------- VALDEMORO --------
    with col2:
        st.subheader("🏥 Valdemoro")

        fpsi_v = st.number_input("Fact PSI", key=mes+"fpsi_v")
        lpsi_v = st.number_input("Lab PSI", key=mes+"lpsi_v")

        var = max((fpsi_v - lpsi_v - 3730),0)*0.3
        bruto_val = var + 741
        neto_val = bruto_val * 0.70

    total_mes = neto_col + neto_val
    st.success(f"💰 TOTAL A COBRAR: {round(total_mes,2)} €")

    total_ingresos += bruto_col + bruto_val
    total_retenido += (bruto_col + bruto_val) * 0.30

    netos.append(total_mes)

    # Guardamos datos del mes
    datos_guardar.append([
        mes, fg, lg, fpsi, lpsi, fpsi_v, lpsi_v, total_mes
    ])

# ---------------- BOTÓN GUARDAR ----------------
if st.button("💾 Guardar en Google Sheets"):

    sheet.clear()

    sheet.append_row(["Mes","FG","LG","FPSI","LPSI","FPSI_V","LPSI_V","TOTAL"])

    for fila in datos_guardar:
        sheet.append_row(fila)

    st.success("Datos guardados en Google Sheets 🔥")

# ---------------- IRPF ----------------
def calcular_irpf(base):
    impuesto = 0
    tramos = [(12450,0.19),(20200,0.24),(35200,0.30),(60000,0.37),(300000,0.45)]
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

# ---------------- RESUMEN ----------------
st.header("📊 HACIENDA")

col1, col2, col3 = st.columns(3)

col1.metric("Ingresos", f"{round(total_ingresos,2)} €")
col2.metric("Retenido", f"{round(total_retenido,2)} €")
col3.metric("IRPF real", f"{round(irpf_real,2)} €")

dif = total_retenido - irpf_real

if dif > 0:
    st.success(f"🟢 Te devolverán: {round(dif,2)} €")
else:
    st.error(f"🔴 Te faltará pagar: {round(abs(dif),2)} €")

# ---------------- GRÁFICA ----------------
st.header("📈 Evolución mensual")

df = pd.DataFrame({
    "Mes": meses,
    "Cobro": netos
})

st.line_chart(df.set_index("Mes"))
