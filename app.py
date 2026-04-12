import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

st.set_page_config(page_title="Facturación PRO", layout="wide")

# ─────────────────────────────────────────
# 🎨 ESTILO
# ─────────────────────────────────────────
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
}
</style>
""", unsafe_allow_html=True)

st.title("💰 Facturación Clínica PRO")

# ─────────────────────────────────────────
# AÑO
# ─────────────────────────────────────────
current_year = datetime.now().year
year = st.selectbox("📅 Año", list(range(2024, current_year + 3)))

# ─────────────────────────────────────────
# GOOGLE SHEETS
# ─────────────────────────────────────────
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

creds = ServiceAccountCredentials.from_json_keyfile_dict(
    dict(st.secrets["gcp_service_account"]), scope
)

client = gspread.authorize(creds)
spreadsheet = client.open_by_url("https://docs.google.com/spreadsheets/d/1JgpD7qiclpmTuLoHDWCIWdtJ5DPdZKeURFwkXv3_e7U/edit")
sheet = spreadsheet.worksheet("Hoja 1")

# ─────────────────────────────────────────
# FUNCIONES
# ─────────────────────────────────────────
def safe_int(x):
    try:
        return int(float(x))
    except:
        return 0

def calc_colmenar(fg, lg, fpsi, lpsi):
    fijo = 800
    variable = max(0,(fg - 1404 - lg)*0.35 + (fpsi - 1428 - lpsi)*0.30)
    bruto = fijo + variable
    neto = bruto * 0.70
    return bruto, neto

def calc_valdemoro(fpsi_v, lpsi_v):
    fijo = 800
    var = max((fpsi_v - lpsi_v - 3730),0)*0.30
    bruto = fijo + var
    neto = bruto * 0.70
    return bruto, neto

def calcular_irpf(base):
    tramos = [(12450,0.19),(20200,0.24),(35200,0.30),(60000,0.37),(9999999,0.45)]
    impuesto = 0
    prev = 0
    for limite,tipo in tramos:
        if base > prev:
            tramo = min(base, limite) - prev
            impuesto += tramo * tipo
            prev = limite
    return impuesto

# ─────────────────────────────────────────
# CARGA DATOS
# ─────────────────────────────────────────
data_sheet = sheet.get_all_records()

datos_por_mes = {}
for row in data_sheet:
    if str(row.get("Año")).strip() == str(year):
        datos_por_mes[str(row.get("Mes")).strip()] = row

meses = ["Enero","Febrero","Marzo","Abril","Mayo","Junio",
         "Julio","Agosto","Septiembre","Octubre","Noviembre","Diciembre"]

total_bruto = 0
total_retenido = 0
netos = []
datos_guardar = []

# ─────────────────────────────────────────
# NAVEGACIÓN
# ─────────────────────────────────────────
tab_dash, tab_meses, tab_irpf = st.tabs(["📊 Dashboard", "📅 Meses", "🧾 Hacienda"])

# ───────── DASHBOARD ─────────
with tab_dash:

    st.header("📊 Resumen anual")

    for mes in meses:
        d = datos_por_mes.get(mes, {})
        bruto_col, neto_col = calc_colmenar(
            safe_int(d.get("FG",0)),
            safe_int(d.get("LG",0)),
            safe_int(d.get("FPSI",0)),
            safe_int(d.get("LPSI",0))
        )
        bruto_val, neto_val = calc_valdemoro(
            safe_int(d.get("FPSI_V",0)),
            safe_int(d.get("LPSI_V",0))
        )

        total_mes = neto_col + neto_val

        total_bruto += bruto_col + bruto_val
        total_retenido += (bruto_col + bruto_val) * 0.30
        netos.append(total_mes)

    col1,col2,col3 = st.columns(3)
    col1.metric("💰 Bruto", round(total_bruto))
    col2.metric("💶 Neto", round(sum(netos)))
    col3.metric("🏦 Retenido", round(total_retenido))

    df = pd.DataFrame({"Mes": meses, "Neto": netos})
    df["Acumulado"] = df["Neto"].cumsum()

    st.line_chart(df.set_index("Mes"))

# ───────── MESES ─────────
with tab_meses:

    tabs_meses = st.tabs(meses)

    for i, mes in enumerate(meses):

        with tabs_meses[i]:

            d = datos_por_mes.get(mes, {})

            col1, col2 = st.columns(2)

            with col1:
                st.markdown('<div class="card-blue">', unsafe_allow_html=True)
                fg = st.number_input("Fact General", value=safe_int(d.get("FG",0)), key=mes+"fg")
                lg = st.number_input("Lab General", value=safe_int(d.get("LG",0)), key=mes+"lg")
                fpsi = st.number_input("Fact PSI", value=safe_int(d.get("FPSI",0)), key=mes+"fpsi")
                lpsi = st.number_input("Lab PSI", value=safe_int(d.get("LPSI",0)), key=mes+"lpsi")

                bruto_col, neto_col = calc_colmenar(fg,lg,fpsi,lpsi)
                st.metric("Colmenar", round(neto_col))
                st.markdown('</div>', unsafe_allow_html=True)

            with col2:
                st.markdown('<div class="card-green">', unsafe_allow_html=True)
                fpsi_v = st.number_input("Fact PSI V", value=safe_int(d.get("FPSI_V",0)), key=mes+"fpsi_v")
                lpsi_v = st.number_input("Lab PSI V", value=safe_int(d.get("LPSI_V",0)), key=mes+"lpsi_v")

                bruto_val, neto_val = calc_valdemoro(fpsi_v,lpsi_v)
                st.metric("Valdemoro", round(neto_val))
                st.markdown('</div>', unsafe_allow_html=True)

            total_mes = round(neto_col + neto_val)
            st.markdown(f'<div class="card-total">TOTAL: {total_mes} €</div>', unsafe_allow_html=True)

            datos_guardar.append([str(year), mes, fg, lg, fpsi, lpsi, fpsi_v, lpsi_v, total_mes])

    if st.button("💾 Guardar"):
        fresh = sheet.get_all_records()
        for fila in datos_guardar:
            año, mes = fila[0], fila[1]
            idx = next((i+2 for i,r in enumerate(fresh)
                        if str(r.get("Año")).strip()==año and str(r.get("Mes")).strip()==mes),None)

            if idx:
                sheet.update(f"A{idx}:I{idx}", [fila])
            else:
                sheet.append_row(fila)

        st.success("Guardado")

# ───────── IRPF ─────────
with tab_irpf:

    base = max(total_bruto - 500 - 2000 - 5550, 0)
    irpf = calcular_irpf(base)
    resultado = total_retenido - irpf

    st.metric("Base", round(base))
    st.metric("IRPF", round(irpf))

    if resultado > 0:
        st.success(f"Te devuelven {round(resultado)} €")
    else:
        st.error(f"A pagar {round(abs(resultado))} €")
