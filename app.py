import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

st.set_page_config(page_title="Facturación PRO", layout="wide")

st.markdown("""
<style>
.stApp { background-color: #0b1220; }
h1, h2, h3 { color: #e6eefc; }

.card-blue {
    background: linear-gradient(135deg, #102a43, #0f1f33);
    border: 1px solid #1f4e79;
    border-radius: 14px;
    padding: 16px;
}
.card-green {
    background: linear-gradient(135deg, #0f2a1f, #0c1f18);
    border: 1px solid #2a7f62;
    border-radius: 14px;
    padding: 16px;
}
.card-total {
    background: linear-gradient(135deg, #2a1f3d, #1b1328);
    border: 1px solid #7a5cff;
    border-radius: 14px;
    padding: 12px;
    text-align: center;
    font-size: 18px;
    color: #cdbfff;
    margin-top: 10px;
    margin-bottom: 14px;
}
[data-testid="stMetric"] {
    background: #111a2b;
    border: 1px solid #1f2a44;
    border-radius: 12px;
    padding: 10px;
}
[data-testid="stSidebar"] {
    background-color: #0e1628;
}
</style>
""", unsafe_allow_html=True)

st.title("💰 Facturación Clínica PRO")

current_year = datetime.now().year
years = list(range(2024, current_year + 3))
year = st.selectbox("📅 Año", years, index=years.index(current_year))

# ─────────────────────────────────────────
# GOOGLE SHEETS
# ─────────────────────────────────────────
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

creds = ServiceAccountCredentials.from_json_keyfile_dict(
    dict(st.secrets["gcp_service_account"]),
    scope
)

client = gspread.authorize(creds)

spreadsheet = client.open_by_url(
    "https://docs.google.com/spreadsheets/d/1JgpD7qiclpmTuLoHDWCIWdtJ5DPdZKeURFwkXv3_e7U/edit"
)

sheet = spreadsheet.worksheet("Hoja 1")

HEADERS = ["Año", "Mes", "FG", "LG", "FPSI", "LPSI", "FPSI_V", "LPSI_V", "TOTAL"]

# Nunca borrar nada
if not sheet.row_values(1):
    sheet.append_row(HEADERS)

# ─────────────────────────────────────────
# FUNCIONES
# ─────────────────────────────────────────
def safe_int(value):
    try:
        if value is None or value == "":
            return 0
        return int(float(value))
    except:
        return 0

def calc_colmenar(fg, lg, fpsi, lpsi):
    fijo = 800
    variable = max(0, (fg - 1404 - lg) * 0.35 + (fpsi - 1428 - lpsi) * 0.30)
    bruto = fijo + variable
    neto = bruto * 0.70
    return bruto, neto

def calc_valdemoro(fpsi_v, lpsi_v):
    fijo = 800  # ✅ CORREGIDO (antes 741)

    var = max((fpsi_v - lpsi_v - 3730), 0) * 0.30
    bruto = fijo + var
    neto = bruto * 0.70
    return bruto, neto

def calcular_irpf(base):
    tramos = [
        (12450, 0.19),
        (20200, 0.24),
        (35200, 0.30),
        (60000, 0.37),
        (999999999, 0.45),
    ]
    impuesto = 0
    anterior = 0
    for limite, tipo in tramos:
        if base > anterior:
            tramo = min(base, limite) - anterior
            impuesto += tramo * tipo
            anterior = limite
    return impuesto

# ─────────────────────────────────────────
# CARGA DATOS (TU VERSIÓN QUE FUNCIONA)
# ─────────────────────────────────────────
try:
    data_sheet = sheet.get_all_records()
except:
    data_sheet = []

datos_por_mes = {}
for row in data_sheet:
    if str(row.get("Año", "")).strip() == str(year):
        mes = str(row.get("Mes", "")).strip()
        if mes:
            datos_por_mes[mes] = row

# ─────────────────────────────────────────
# APP
# ─────────────────────────────────────────
meses = [
    "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
    "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
]

total_ingresos = 0
total_retenido = 0
netos = []
datos_guardar = []

for mes in meses:
    st.header(f"📅 {mes}")

    d = datos_por_mes.get(mes, {})

    col1, col2 = st.columns(2, gap="large")

    # 🔵 COLMENAR
    with col1:
        st.markdown('<div class="card-blue">', unsafe_allow_html=True)
        st.subheader("🔵 Colmenar")

        fg = st.number_input("Fact General €", value=safe_int(d.get("FG", 0)), key=f"{mes}_fg")
        lg = st.number_input("Lab General €", value=safe_int(d.get("LG", 0)), key=f"{mes}_lg")
        fpsi = st.number_input("Fact PSI €", value=safe_int(d.get("FPSI", 0)), key=f"{mes}_fpsi")
        lpsi = st.number_input("Lab PSI €", value=safe_int(d.get("LPSI", 0)), key=f"{mes}_lpsi")

        bruto_col, neto_col = calc_colmenar(fg, lg, fpsi, lpsi)

        st.metric("💶 Neto Colmenar", round(neto_col))
        st.markdown('</div>', unsafe_allow_html=True)

    # 🟢 VALDEMORO
    with col2:
        st.markdown('<div class="card-green">', unsafe_allow_html=True)
        st.subheader("🟢 Valdemoro")

        fpsi_v = st.number_input("Fact PSI V €", value=safe_int(d.get("FPSI_V", 0)), key=f"{mes}_fpsi_v")
        lpsi_v = st.number_input("Lab PSI V €", value=safe_int(d.get("LPSI_V", 0)), key=f"{mes}_lpsi_v")

        bruto_val, neto_val = calc_valdemoro(fpsi_v, lpsi_v)

        st.metric("💶 Neto Valdemoro", round(neto_val))
        st.markdown('</div>', unsafe_allow_html=True)

    total_mes = round(neto_col + neto_val)

    st.markdown(f'<div class="card-total">💰 TOTAL MES: {total_mes} €</div>', unsafe_allow_html=True)

    total_ingresos += bruto_col + bruto_val
    total_retenido += (bruto_col + bruto_val) * 0.30

    netos.append(total_mes)

    datos_guardar.append([str(year), mes, fg, lg, fpsi, lpsi, fpsi_v, lpsi_v, total_mes])

# ─────────────────────────────────────────
# GUARDAR
# ─────────────────────────────────────────
if st.button("💾 Guardar"):

    data_sheet = sheet.get_all_records()

    for fila in datos_guardar:
        año, mes = fila[0], fila[1]
        fila_encontrada = None

        for i, row in enumerate(data_sheet):
            if str(row.get("Año", "")).strip() == año and str(row.get("Mes", "")).strip() == mes:
                fila_encontrada = i + 2
                break

        if fila_encontrada:
            sheet.update(f"A{fila_encontrada}:I{fila_encontrada}", [fila])
        else:
            sheet.append_row(fila)

    st.success("Guardado correcto 🔥")

# ─────────────────────────────────────────
# IRPF
# ─────────────────────────────────────────
st.header("📊 Hacienda")

base = max(total_ingresos - 500 - 2000 - 5550, 0)
irpf_real = calcular_irpf(base)
resultado = total_retenido - irpf_real

c1, c2, c3, c4 = st.columns(4)
c1.metric("Ingresos", round(total_ingresos))
c2.metric("Retenido", round(total_retenido))
c3.metric("Base imponible", round(base))
c4.metric("IRPF real", round(irpf_real))

if resultado > 0:
    st.success(f"🟢 Hacienda te devuelve: {round(resultado)} €")
else:
    st.error(f"🔴 A pagar: {round(abs(resultado))} €")

# ─────────────────────────────────────────
# GRÁFICA
# ─────────────────────────────────────────
df = pd.DataFrame({"Mes": meses, "Cobro": netos})
st.line_chart(df.set_index("Mes"))
