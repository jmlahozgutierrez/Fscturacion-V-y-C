import streamlit as st
import pandas as pd
import json
import os

st.set_page_config(page_title="Facturación PRO", layout="wide")

st.title("💰 Facturación Clínica PRO")

FILE = "datos.json"

meses = ["Enero","Febrero","Marzo","Abril","Mayo","Junio",
         "Julio","Agosto","Septiembre","Octubre","Noviembre","Diciembre"]

# ---------------- CARGAR ----------------
if os.path.exists(FILE):
    with open(FILE, "r") as f:
        data = json.load(f)
else:
    data = {mes:{} for mes in meses}

total_ingresos = 0
total_retenido = 0
netos = []

# ---------------- LOOP ----------------
for mes in meses:

    st.header(f"📅 {mes}")

    col1, col2 = st.columns(2)

    # -------- COLMENAR (ANEXO SOLO) --------
    with col1:
        st.subheader("🏥 Colmenar")

        fg = st.number_input("Fact General", value=data[mes].get("fg",0.0), key=mes+"fg")
        lg = st.number_input("Lab General", value=data[mes].get("lg",0.0), key=mes+"lg")
        fpsi = st.number_input("Fact PSI", value=data[mes].get("fpsi",0.0), key=mes+"fpsi")
        lpsi = st.number_input("Lab PSI", value=data[mes].get("lpsi",0.0), key=mes+"lpsi")

        data[mes]["fg"] = fg
        data[mes]["lg"] = lg
        data[mes]["fpsi"] = fpsi
        data[mes]["lpsi"] = lpsi

        fijo = 800
        variable = max(0,(fg - 1404.33 - lg)*0.35 + (fpsi - 1428.33 - lpsi)*0.3)

        bruto_col = fijo + variable
        neto_col = bruto_col * 0.70

    # -------- VALDEMORO --------
    with col2:
        st.subheader("🏥 Valdemoro")

        fpsi_v = st.number_input("Fact PSI", value=data[mes].get("fpsi_v",0.0), key=mes+"fpsi_v")
        lpsi_v = st.number_input("Lab PSI", value=data[mes].get("lpsi_v",0.0), key=mes+"lpsi_v")

        data[mes]["fpsi_v"] = fpsi_v
        data[mes]["lpsi_v"] = lpsi_v

        var = max((fpsi_v - lpsi_v - 3730),0)*0.3
        bruto_val = var + 741
        neto_val = bruto_val * 0.70

    # -------- TOTAL MES --------
    total_mes = neto_col + neto_val
    st.success(f"💰 TOTAL A COBRAR: {round(total_mes,2)} €")

    total_ingresos += bruto_col + bruto_val
    total_retenido += (bruto_col + bruto_val) * 0.30

    netos.append(total_mes)

# ---------------- GUARDAR ----------------
with open(FILE, "w") as f:
    json.dump(data, f)

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
import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials

st.title("Test conexión Google Sheets")

scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

creds = ServiceAccountCredentials.from_json_keyfile_dict(
    st.secrets["gcp_service_account"], scope
)

client = gspread.authorize(creds)

# 👇 IMPORTANTE: pon EXACTO el nombre de tu sheet
sheet = client.open("Facturacion PRO").sheet1

data = sheet.get_all_records()

st.write("✅ Conectado correctamente")
st.write(data)
