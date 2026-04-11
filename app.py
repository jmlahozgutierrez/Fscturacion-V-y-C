import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

st.set_page_config(page_title="Facturación Clínica PRO", layout="wide")

# ─────────────────────────────────────────
# GOOGLE SHEETS (LECTURA ROBUSTA)
# ─────────────────────────────────────────
@st.cache_resource
def get_data():
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]

    creds = ServiceAccountCredentials.from_json_keyfile_dict(
        dict(st.secrets["gcp_service_account"]), scope
    )

    client = gspread.authorize(creds)

    sheet = client.open_by_url(
        "https://docs.google.com/spreadsheets/d/1JgpD7qiclpmTuLoHDWCIWdtJ5DPdZKeURFwkXv3_e7U/edit"
    ).sheet1

    data = sheet.get_all_values()

    headers = data[0]
    rows = data[1:]

    df = pd.DataFrame(rows, columns=headers)

    return df, sheet

# ─────────────────────────────────────────
# UTIL
# ─────────────────────────────────────────
def safe_int(x):
    try:
        return int(float(x))
    except:
        return 0

# ─────────────────────────────────────────
# APP
# ─────────────────────────────────────────
st.title("💰 Facturación Clínica PRO")

current_year = datetime.now().year
year = st.selectbox("Año", list(range(2024, current_year+2)), index=1)

df, sheet = get_data()

# 🔥 LIMPIEZA CLAVE
df["Año"] = df["Año"].apply(safe_int)
df["Mes"] = df["Mes"].astype(str).str.strip().str.lower()

df = df[df["Año"] == year]

datos_por_mes = {
    row["Mes"]: row for _, row in df.iterrows()
}

MESES = [
    "enero","febrero","marzo","abril","mayo","junio",
    "julio","agosto","septiembre","octubre","noviembre","diciembre"
]

total_bruto = 0
total_retenido = 0
netos = []
datos_guardar = []

for mes in MESES:

    st.header(mes.capitalize())

    d = datos_por_mes.get(mes, {})

    col1, col2 = st.columns(2)

    with col1:
        fg = st.number_input("Fact General", value=safe_int(d.get("FG",0)), key=mes+"fg")
        lg = st.number_input("Lab General", value=safe_int(d.get("LG",0)), key=mes+"lg")
        fpsi = st.number_input("Fact PSI", value=safe_int(d.get("FPSI",0)), key=mes+"fpsi")
        lpsi = st.number_input("Lab PSI", value=safe_int(d.get("LPSI",0)), key=mes+"lpsi")

    with col2:
        fpsi_v = st.number_input("Fact PSI V", value=safe_int(d.get("FPSI_V",0)), key=mes+"fpsi_v")
        lpsi_v = st.number_input("Lab PSI V", value=safe_int(d.get("LPSI_V",0)), key=mes+"lpsi_v")

    # cálculo simple para probar
    total_mes = fg - lg + fpsi - lpsi + fpsi_v - lpsi_v

    st.success(f"TOTAL: {total_mes}")

    datos_guardar.append([year, mes.capitalize(), fg, lg, fpsi, lpsi, fpsi_v, lpsi_v, total_mes])

# ─────────────────────────────────────────
# GUARDAR
# ─────────────────────────────────────────
if st.button("Guardar"):
    for fila in datos_guardar:
        sheet.append_row(fila)

    st.success("Guardado")

# DEBUG
st.write("Datos cargados:", datos_por_mes)
