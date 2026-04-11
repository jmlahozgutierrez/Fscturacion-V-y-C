import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

st.set_page_config(page_title="Facturación Clínica PRO", layout="wide")

# ─────────────────────────────────────────
# GOOGLE SHEETS
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
# CÁLCULOS REALES
# ─────────────────────────────────────────
def calc_colaboradora(fg, lg, fpsi, lpsi):
    fijo = 800

    minimo_general  = 16852 / 11
    minimo_prostodo = 17140 / 11

    var_gen = max(0, (fg - minimo_general)) * 0.35 - (lg * 0.35)
    var_psi = max(0, (fpsi - minimo_prostodo)) * 0.30 - (lpsi * 0.30)

    variable = max(0, var_gen) + max(0, var_psi)

    bruto = fijo + variable
    neto  = bruto * 0.70

    return bruto, neto

def calc_voluntaria(fpsi_v, lpsi_v):
    fijo = 800

    minimo_valdemoro = 41036 / 11

    var = max(0, (fpsi_v - minimo_valdemoro)) * 0.30 - (lpsi_v * 0.30)

    variable = max(0, var)

    bruto = fijo + variable
    neto  = bruto * 0.70

    return bruto, neto

# ─────────────────────────────────────────
# APP
# ─────────────────────────────────────────
st.title("💰 Facturación Clínica PRO")

current_year = datetime.now().year
year = st.selectbox("Año", list(range(2024, current_year+2)), index=1)

df, sheet = get_data()

# LIMPIEZA
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

for mes in MESES:

    st.header(mes.capitalize())

    d = datos_por_mes.get(mes, {})

    col1, col2 = st.columns(2)

    with col1:
        fg = st.number_input("Fact General", value=safe_int(d.get("FG",0)), key=mes+"fg")
        lg = st.number_input("Lab General", value=safe_int(d.get("LG",0)), key=mes+"lg")
        fpsi = st.number_input("Fact PSI", value=safe_int(d.get("FPSI",0)), key=mes+"fpsi")
        lpsi = st.number_input("Lab PSI", value=safe_int(d.get("LPSI",0)), key=mes+"lpsi")

        bruto_col, neto_col = calc_colaboradora(fg, lg, fpsi, lpsi)

        st.metric("Neto Colmenar", round(neto_col))

    with col2:
        fpsi_v = st.number_input("Fact PSI V", value=safe_int(d.get("FPSI_V",0)), key=mes+"fpsi_v")
        lpsi_v = st.number_input("Lab PSI V", value=safe_int(d.get("LPSI_V",0)), key=mes+"lpsi_v")

        bruto_vol, neto_vol = calc_voluntaria(fpsi_v, lpsi_v)

        st.metric("Neto Valdemoro", round(neto_vol))

    total_mes = round(neto_col + neto_vol)
    st.success(f"TOTAL: {total_mes} €")

    total_bruto += bruto_col + bruto_vol
    total_retenido += (bruto_col + bruto_vol) * 0.30

    netos.append(total_mes)

# ─────────────────────────────────────────
# RESUMEN
# ─────────────────────────────────────────
st.divider()

st.metric("Bruto total", round(total_bruto))
st.metric("Retenido", round(total_retenido))
st.metric("Neto total", round(total_bruto - total_retenido))

df_chart = pd.DataFrame({"Mes": MESES, "Neto": netos})
st.line_chart(df_chart.set_index("Mes"))
