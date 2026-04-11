import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime


# ─────────────────────────────────────────
#  CONFIG
# ─────────────────────────────────────────
st.set_page_config(
    page_title="Facturación Clínica PRO",
    layout="wide",
    page_icon="💰"
)

# ─────────────────────────────────────────
#  CSS
# ─────────────────────────────────────────
st.markdown("""
<style>
.stApp { background-color: #060f1a; }
html, body, [class*="css"] { color: #c8d8e8; }
[data-testid="stSidebar"] { background-color: #0a1929; border-right: 1px solid #1a3050; }
[data-testid="stMetric"] {
    background: linear-gradient(135deg, #0f2137, #0a1929);
    border: 1px solid #1a3050;
    border-radius: 12px;
    padding: 16px 20px;
}
[data-testid="stMetricLabel"] { color: #7c8a9e !important; font-size: 11px !important; }
[data-testid="stMetricValue"] { color: #7eb8f7 !important; }
input[type="number"] {
    background-color: #0d1b2a !important;
    border: 1px solid #1e3a5f !important;
    color: #e8f0fe !important;
}
.stButton > button {
    background: #0e3020 !important;
    border: 1px solid #2a7040 !important;
    color: #4ac9a9 !important;
}
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────
#  GOOGLE SHEETS
# ─────────────────────────────────────────
@st.cache_resource
def get_sheet():
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(
        dict(st.secrets["gcp_service_account"]), scope
    )
    client = gspread.authorize(creds)
    return client.open_by_url(
        "https://docs.google.com/spreadsheets/d/1JgpD7qiclpmTuLoHDWCIWdtJ5DPdZKeURFwkXv3_e7U/edit"
    ).worksheet("Hoja 1")


def ensure_headers(sheet, headers):
    if sheet.row_values(1) != headers:
        sheet.clear()
        sheet.append_row(headers)


# ─────────────────────────────────────────
#  CÁLCULOS CORRECTOS (AQUÍ ESTÁ LA CLAVE)
# ─────────────────────────────────────────
def calc_colaboradora(fg, lg, fpsi, lpsi):
    fijo = 800

    minimo_general  = 16852 / 11
    minimo_prostodo = 17140 / 11

    # VARIABLES SEPARADAS (IMPORTANTE)
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
#  CONSTANTES
# ─────────────────────────────────────────
HEADERS = ["Año","Mes","FG","LG","FPSI","LPSI","FPSI_V","LPSI_V","TOTAL"]
MESES   = ["Enero","Febrero","Marzo","Abril","Mayo","Junio",
           "Julio","Agosto","Septiembre","Octubre","Noviembre","Diciembre"]


# ─────────────────────────────────────────
#  HEADER
# ─────────────────────────────────────────
col_title, col_year = st.columns([3, 1])
with col_title:
    st.title("💰 Facturación Clínica PRO")
with col_year:
    current_year = datetime.now().year
    years = list(range(2024, current_year + 3))
    year = st.selectbox("📅 Año", years, index=years.index(current_year))

st.divider()


# ─────────────────────────────────────────
#  DATOS
# ─────────────────────────────────────────
sheet = get_sheet()
ensure_headers(sheet, HEADERS)

try:
    data_sheet = sheet.get_all_records()
except:
    data_sheet = []

datos_por_mes = {
    row["Mes"]: row
    for row in data_sheet
    if str(row.get("Año")) == str(year)
}


# ─────────────────────────────────────────
#  UI
# ─────────────────────────────────────────
total_bruto = 0
total_retenido = 0
netos = []
brutos_col = []
brutos_vol = []
datos_guardar = []

for mes in MESES:

    st.header(f"📅 {mes}")

    col1, col2 = st.columns(2)

    d = datos_por_mes.get(mes, {})

    with col1:
        fg   = st.number_input("Fact General €", value=int(d.get("FG",0)), step=1, key=mes+"fg")
        lg   = st.number_input("Lab General €", value=int(d.get("LG",0)), step=1, key=mes+"lg")
        fpsi = st.number_input("Fact PSI €", value=int(d.get("FPSI",0)), step=1, key=mes+"fpsi")
        lpsi = st.number_input("Lab PSI €", value=int(d.get("LPSI",0)), step=1, key=mes+"lpsi")

        bruto_col, neto_col = calc_colaboradora(fg, lg, fpsi, lpsi)
        st.metric("Neto Colmenar", f"{round(neto_col)} €")

    with col2:
        fpsi_v = st.number_input("Fact PSI V €", value=int(d.get("FPSI_V",0)), step=1, key=mes+"fpsi_v")
        lpsi_v = st.number_input("Lab PSI V €", value=int(d.get("LPSI_V",0)), step=1, key=mes+"lpsi_v")

        bruto_vol, neto_vol = calc_voluntaria(fpsi_v, lpsi_v)
        st.metric("Neto Valdemoro", f"{round(neto_vol)} €")

    total_mes = round(neto_col + neto_vol)
    st.success(f"💰 TOTAL: {total_mes} €")

    total_bruto += bruto_col + bruto_vol
    total_retenido += (bruto_col + bruto_vol) * 0.30

    netos.append(total_mes)
    brutos_col.append(round(bruto_col))
    brutos_vol.append(round(bruto_vol))

    datos_guardar.append([str(year), mes, fg, lg, fpsi, lpsi, fpsi_v, lpsi_v, total_mes])


# ─────────────────────────────────────────
#  GUARDAR
# ─────────────────────────────────────────
if st.button("💾 Guardar"):

    fresh = sheet.get_all_records()

    for fila in datos_guardar:
        año, mes = fila[0], fila[1]

        idx = next(
            (i+2 for i, r in enumerate(fresh)
             if str(r.get("Año")) == año and r.get("Mes") == mes),
            None
        )

        if idx:
            sheet.update(f"A{idx}:I{idx}", [fila])
        else:
            sheet.append_row(fila)

    st.success("Guardado correcto 🔥")


# ─────────────────────────────────────────
#  RESUMEN
# ─────────────────────────────────────────
st.divider()

st.metric("💼 Bruto total", round(total_bruto))
st.metric("🏦 Retenido", round(total_retenido))
st.metric("✅ Neto total", round(total_bruto - total_retenido))

df = pd.DataFrame({
    "Mes": MESES,
    "Neto": netos
})

st.line_chart(df.set_index("Mes"))
