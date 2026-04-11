import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

# ─────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────
st.set_page_config(page_title="Facturación Clínica PRO", layout="wide")

# ─────────────────────────────────────────
# GOOGLE SHEETS
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

    spreadsheet = client.open_by_url(
        "https://docs.google.com/spreadsheets/d/1JgpD7qiclpmTuLoHDWCIWdtJ5DPdZKeURFwkXv3_e7U/edit"
    )

    return spreadsheet.sheet1


def ensure_headers(sheet, headers):
    if not sheet.row_values(1):
        sheet.append_row(headers)


# ─────────────────────────────────────────
# UTILIDAD CLAVE (FIX)
# ─────────────────────────────────────────
def safe_int(value):
    try:
        return int(float(value))
    except:
        return 0


# ─────────────────────────────────────────
# CÁLCULOS
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
# IRPF
# ─────────────────────────────────────────
def calcular_irpf_madrid(bruto, retenido, gastos=500):
    gasto_general = 2000
    minimo_personal = 5550

    base = bruto - gastos - gasto_general - minimo_personal
    base = max(0, base)

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

    resultado = retenido - impuesto

    return base, impuesto, resultado


# ─────────────────────────────────────────
# TRAMOS
# ─────────────────────────────────────────
def obtener_tramo(base):
    if base <= 12450:
        return 1
    elif base <= 20200:
        return 2
    elif base <= 35200:
        return 3
    elif base <= 60000:
        return 4
    else:
        return 5


# ─────────────────────────────────────────
# CONSTANTES
# ─────────────────────────────────────────
HEADERS = ["Año","Mes","FG","LG","FPSI","LPSI","FPSI_V","LPSI_V","TOTAL"]

MESES = [
    "Enero","Febrero","Marzo","Abril","Mayo","Junio",
    "Julio","Agosto","Septiembre","Octubre","Noviembre","Diciembre"
]


# ─────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────
st.title("💰 Facturación Clínica PRO")

current_year = datetime.now().year
year = st.selectbox("Año", list(range(2024, current_year+2)), index=1)


# ─────────────────────────────────────────
# DATOS (FIX TOTAL)
# ─────────────────────────────────────────
sheet = get_sheet()
ensure_headers(sheet, HEADERS)

data_sheet = sheet.get_all_records()

datos_por_mes = {}

for row in data_sheet:
    try:
        año_sheet = int(float(row.get("Año", 0)))
    except:
        continue

    mes_sheet = str(row.get("Mes", "")).strip().lower()

    if año_sheet == year and mes_sheet:
        datos_por_mes[mes_sheet] = row


# ─────────────────────────────────────────
# LOOP MESES
# ─────────────────────────────────────────
total_bruto = 0
total_retenido = 0
netos = []
datos_guardar = []

tramo_anterior = 1

for mes in MESES:

    st.header(mes)

    col1, col2 = st.columns(2)
    d = datos_por_mes.get(mes.lower(), {})

    with col1:
        fg   = st.number_input("Fact General €", value=safe_int(d.get("FG",0)), key=mes+"fg")
        lg   = st.number_input("Lab General €", value=safe_int(d.get("LG",0)), key=mes+"lg")
        fpsi = st.number_input("Fact PSI €", value=safe_int(d.get("FPSI",0)), key=mes+"fpsi")
        lpsi = st.number_input("Lab PSI €", value=safe_int(d.get("LPSI",0)), key=mes+"lpsi")

        bruto_col, neto_col = calc_colaboradora(fg, lg, fpsi, lpsi)
        st.metric("Neto Colmenar", round(neto_col))

    with col2:
        fpsi_v = st.number_input("Fact PSI V €", value=safe_int(d.get("FPSI_V",0)), key=mes+"fpsi_v")
        lpsi_v = st.number_input("Lab PSI V €", value=safe_int(d.get("LPSI_V",0)), key=mes+"lpsi_v")

        bruto_vol, neto_vol = calc_voluntaria(fpsi_v, lpsi_v)
        st.metric("Neto Valdemoro", round(neto_vol))

    total_mes = round(neto_col + neto_vol)
    st.success(f"TOTAL: {total_mes} €")

    total_bruto += bruto_col + bruto_vol
    total_retenido += (bruto_col + bruto_vol) * 0.30

    netos.append(total_mes)

    # ALERTAS
    base_acumulada = total_bruto - 500 - 2000 - 5550
    base_acumulada = max(0, base_acumulada)

    tramo_actual = obtener_tramo(base_acumulada)

    if tramo_actual > tramo_anterior:
        st.error(f"🚨 Has subido al tramo {tramo_actual}")

    limites = [12450, 20200, 35200, 60000]

    for limite in limites:
        if base_acumulada < limite:
            distancia = limite - base_acumulada
            if distancia < 3000:
                st.warning(f"⚠️ Estás a {round(distancia)} € de subir tramo")
            break

    tramo_anterior = tramo_actual

    datos_guardar.append([
        str(year), mes, fg, lg, fpsi, lpsi, fpsi_v, lpsi_v, total_mes
    ])


# ─────────────────────────────────────────
# GUARDAR
# ─────────────────────────────────────────
if st.button("Guardar"):

    fresh = sheet.get_all_records()

    for fila in datos_guardar:
        año, mes = fila[0], fila[1]

        idx = next(
            (i+2 for i, r in enumerate(fresh)
             if str(r.get("Año")) == año and str(r.get("Mes")).strip().lower() == mes.lower()),
            None
        )

        if idx:
            sheet.update(f"A{idx}:I{idx}", [fila])
        else:
            sheet.append_row(fila)

    st.success("Guardado correcto")


# ─────────────────────────────────────────
# RESUMEN
# ─────────────────────────────────────────
st.divider()

base, irpf_real, resultado = calcular_irpf_madrid(
    total_bruto,
    total_retenido
)

st.metric("Bruto total", round(total_bruto))
st.metric("Retenido", round(total_retenido))
st.metric("Base imponible", round(base))
st.metric("IRPF real", round(irpf_real))

if resultado > 0:
    st.success(f"Hacienda te devuelve: {round(resultado)} €")
else:
    st.error(f"A pagar: {round(abs(resultado))} €")

df = pd.DataFrame({"Mes": MESES, "Neto": netos})
st.line_chart(df.set_index("Mes"))
