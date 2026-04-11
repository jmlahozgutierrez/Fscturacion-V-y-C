import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

st.set_page_config(page_title="Facturación PRO", layout="wide")

# ─────────────────────────────────────────
# 🎨 ESTILO PREMIUM
# ─────────────────────────────────────────
st.markdown("""
<style>
.stApp { background-color: #0b1220; }

h1 { color: #e6eefc; }

/* Cards */
.card-blue {
    background: linear-gradient(135deg, #102a43, #0f1f33);
    border: 1px solid #1f4e79;
    border-radius: 12px;
    padding: 15px;
}
.card-green {
    background: linear-gradient(135deg, #0f2a1f, #0c1f18);
    border: 1px solid #2a7f62;
    border-radius: 12px;
    padding: 15px;
}
.card-total {
    background: linear-gradient(135deg, #2a1f3d, #1b1328);
    border: 1px solid #7a5cff;
    border-radius: 12px;
    padding: 10px;
    text-align: center;
    font-size: 18px;
    color: #cdbfff;
    margin-top: 10px;
}

/* Métricas */
[data-testid="stMetric"] {
    background: #111a2b;
    border-radius: 10px;
    padding: 10px;
}
</style>
""", unsafe_allow_html=True)

st.title("💰 Facturación Clínica PRO")

# ─────────────────────────────────────────
# AÑO
# ─────────────────────────────────────────
current_year = datetime.now().year
year = st.selectbox("📅 Año", list(range(2024, current_year + 3)), index=1)

# ─────────────────────────────────────────
# CONEXIÓN SHEET
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

sheet = client.open_by_url(
    "https://docs.google.com/spreadsheets/d/1JgpD7qiclpmTuLoHDWCIWdtJ5DPdZKeURFwkXv3_e7U/edit"
).worksheet("Hoja 1")

# Cabecera segura
headers = ["Año","Mes","FG","LG","FPSI","LPSI","FPSI_V","LPSI_V","TOTAL"]
if not sheet.row_values(1):
    sheet.append_row(headers)

# ─────────────────────────────────────────
# CARGA DATOS
# ─────────────────────────────────────────
data_sheet = sheet.get_all_records()

datos_por_mes = {}
for row in data_sheet:
    if str(row.get("Año")).strip() == str(year):
        mes = str(row.get("Mes")).strip()
        datos_por_mes[mes] = row

meses = ["Enero","Febrero","Marzo","Abril","Mayo","Junio",
         "Julio","Agosto","Septiembre","Octubre","Noviembre","Diciembre"]

total_ingresos = 0
total_retenido = 0
netos = []
datos_guardar = []

# ─────────────────────────────────────────
# LOOP PRINCIPAL
# ─────────────────────────────────────────
for mes in meses:

    st.header(f"📅 {mes}")

    col1, col2 = st.columns(2, gap="large")
    d = datos_por_mes.get(mes, {})

    # 🔵 COLMENAR
    with col1:
        st.markdown('<div class="card-blue">', unsafe_allow_html=True)
        st.subheader("🔵 Colmenar")

        fg = st.number_input("Fact General €", value=int(d.get("FG",0)), key=mes+"fg")
        lg = st.number_input("Lab General €", value=int(d.get("LG",0)), key=mes+"lg")
        fpsi = st.number_input("Fact PSI €", value=int(d.get("FPSI",0)), key=mes+"fpsi")
        lpsi = st.number_input("Lab PSI €", value=int(d.get("LPSI",0)), key=mes+"lpsi")

        fijo = 800
        variable = max(0,(fg - 1404 - lg)*0.35 + (fpsi - 1428 - lpsi)*0.30)

        bruto_col = fijo + variable
        neto_col = bruto_col * 0.70

        st.metric("💶 Neto Colmenar", round(neto_col))
        st.markdown('</div>', unsafe_allow_html=True)

    # 🟢 VALDEMORO
    with col2:
        st.markdown('<div class="card-green">', unsafe_allow_html=True)
        st.subheader("🟢 Valdemoro")

        fpsi_v = st.number_input("Fact PSI V €", value=int(d.get("FPSI_V",0)), key=mes+"fpsi_v")
        lpsi_v = st.number_input("Lab PSI V €", value=int(d.get("LPSI_V",0)), key=mes+"lpsi_v")

        var = max((fpsi_v - lpsi_v - 3730),0)*0.30
        bruto_val = var + 741
        neto_val = bruto_val * 0.70

        st.metric("💶 Neto Valdemoro", round(neto_val))
        st.markdown('</div>', unsafe_allow_html=True)

    total_mes = round(neto_col + neto_val)

    st.markdown(f'<div class="card-total">💰 TOTAL MES: {total_mes} €</div>', unsafe_allow_html=True)

    total_ingresos += bruto_col + bruto_val
    total_retenido += (bruto_col + bruto_val) * 0.30
    netos.append(total_mes)

    datos_guardar.append([
        str(year), mes, fg, lg, fpsi, lpsi, fpsi_v, lpsi_v, total_mes
    ])

# ─────────────────────────────────────────
# GUARDAR
# ─────────────────────────────────────────
if st.button("💾 Guardar"):

    data_sheet = sheet.get_all_records()

    for fila in datos_guardar:

        año, mes = fila[0], fila[1]
        fila_idx = None

        for i, row in enumerate(data_sheet):
            if str(row.get("Año")).strip() == año and str(row.get("Mes")).strip() == mes:
                fila_idx = i + 2
                break

        if fila_idx:
            sheet.update(f"A{fila_idx}:I{fila_idx}", [fila])
        else:
            sheet.append_row(fila)

    st.success("Guardado correcto 🔥")

# ─────────────────────────────────────────
# IRPF
# ─────────────────────────────────────────
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

base = max(total_ingresos - 500 - 2000 - 5550, 0)
irpf_real = calcular_irpf(base)
resultado = total_retenido - irpf_real

colA, colB, colC = st.columns(3)
colA.metric("Ingresos", round(total_ingresos))
colB.metric("Retenido", round(total_retenido))
colC.metric("Base", round(base))

if resultado > 0:
    st.success(f"🟢 Hacienda te devuelve: {round(resultado)} €")
else:
    st.error(f"🔴 A pagar: {round(abs(resultado))} €")

# ─────────────────────────────────────────
# GRÁFICA
# ─────────────────────────────────────────
df = pd.DataFrame({"Mes": meses, "Cobro": netos})
st.line_chart(df.set_index("Mes"))
