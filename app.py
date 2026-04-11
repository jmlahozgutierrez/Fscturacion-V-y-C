import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

st.set_page_config(page_title="Facturación PRO", layout="wide")

st.title("💰 Facturación Clínica PRO")

# ---------------- AÑO ----------------
current_year = datetime.now().year
years = list(range(2024, current_year + 3))
year = st.selectbox("📅 Año", years, index=years.index(current_year))

# ---------------- CONEXIÓN ----------------
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

creds = ServiceAccountCredentials.from_json_keyfile_dict(
    dict(st.secrets["gcp_service_account"]),
    scope
)

client = gspread.authorize(creds)

sheet = client.open_by_url(
    "https://docs.google.com/spreadsheets/d/1JgpD7qiclpmTuLoHDWCIWdtJ5DPdZKeURFwkXv3_e7U/edit"
).worksheet("Hoja 1")

# ---------------- CABECERA SEGURA ----------------
headers = ["Año","Mes","FG","LG","FPSI","LPSI","FPSI_V","LPSI_V","TOTAL"]

if not sheet.row_values(1):
    sheet.append_row(headers)

# ---------------- CARGAR DATOS ----------------
try:
    data_sheet = sheet.get_all_records()
except:
    data_sheet = []

datos_por_mes = {}

for row in data_sheet:
    if str(row.get("Año")).strip() == str(year):
        mes_limpio = str(row.get("Mes", "")).strip()
        datos_por_mes[mes_limpio] = row

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

    d = datos_por_mes.get(mes.strip(), {})

    with col1:
        fg = st.number_input("Fact General €", value=int(d.get("FG", 0)), step=1, key=mes+"fg")
        lg = st.number_input("Lab General €", value=int(d.get("LG", 0)), step=1, key=mes+"lg")
        fpsi = st.number_input("Fact PSI €", value=int(d.get("FPSI", 0)), step=1, key=mes+"fpsi")
        lpsi = st.number_input("Lab PSI €", value=int(d.get("LPSI", 0)), step=1, key=mes+"lpsi")

        fijo = 800
        variable = max(0,(fg - 1404 - lg)*0.35 + (fpsi - 1428 - lpsi)*0.30)

        bruto_col = fijo + variable
        neto_col = bruto_col * 0.70

        st.metric("Neto Colmenar", round(neto_col))

    with col2:
        fpsi_v = st.number_input("Fact PSI V €", value=int(d.get("FPSI_V", 0)), step=1, key=mes+"fpsi_v")
        lpsi_v = st.number_input("Lab PSI V €", value=int(d.get("LPSI_V", 0)), step=1, key=mes+"lpsi_v")

        var = max((fpsi_v - lpsi_v - 3730),0)*0.30
        bruto_val = var + 741
        neto_val = bruto_val * 0.70

        st.metric("Neto Valdemoro", round(neto_val))

    total_mes = round(neto_col + neto_val)
    st.success(f"💰 TOTAL: {total_mes} €")

    total_ingresos += bruto_col + bruto_val
    total_retenido += (bruto_col + bruto_val) * 0.30

    netos.append(total_mes)

    # 🚨 ALERTA TRAMOS
    base_acumulada = total_ingresos - 500 - 2000 - 5550
    base_acumulada = max(0, base_acumulada)

    if 18000 < base_acumulada < 20200:
        st.warning("⚠️ Cerca de subir a tramo 24%")

    if 33000 < base_acumulada < 35200:
        st.warning("⚠️ Cerca de subir a tramo 30%")

    if base_acumulada > 60000:
        st.error("🚨 Tramo alto 37%")

    datos_guardar.append([
        str(year), mes, fg, lg, fpsi, lpsi, fpsi_v, lpsi_v, total_mes
    ])

# ---------------- GUARDAR ----------------
if st.button("💾 Guardar"):

    data_sheet = sheet.get_all_records()

    for fila in datos_guardar:

        año = fila[0]
        mes = fila[1]

        fila_encontrada = None

        for i, row in enumerate(data_sheet):
            if str(row.get("Año")).strip() == año and str(row.get("Mes")).strip() == mes:
                fila_encontrada = i + 2
                break

        if fila_encontrada:
            sheet.update(f"A{fila_encontrada}:I{fila_encontrada}", [fila])
        else:
            sheet.append_row(fila)

    st.success("Guardado correcto 🔥")

# ---------------- IRPF ----------------
st.header("📊 Hacienda")

def calcular_irpf(base):
    tramos = [
        (12450, 0.19),
        (20200, 0.24),
        (35200, 0.30),
        (60000, 0.37),
        (9999999, 0.45)
    ]

    impuesto = 0
    anterior = 0

    for limite, tipo in tramos:
        if base > anterior:
            tramo = min(base, limite) - anterior
            impuesto += tramo * tipo
            anterior = limite

    return impuesto

base = total_ingresos - 500 - 2000 - 5550
base = max(base, 0)

irpf_real = calcular_irpf(base)
resultado = total_retenido - irpf_real

st.metric("Ingresos", round(total_ingresos))
st.metric("Retenido", round(total_retenido))
st.metric("Base imponible", round(base))
st.metric("IRPF real", round(irpf_real))

if resultado > 0:
    st.success(f"🟢 Hacienda te devuelve: {round(resultado)} €")
else:
    st.error(f"🔴 A pagar: {round(abs(resultado))} €")

# ---------------- GRÁFICA ----------------
df = pd.DataFrame({
    "Mes": meses,
    "Cobro": netos
})

st.line_chart(df.set_index("Mes"))
