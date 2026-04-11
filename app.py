import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

# Configuración inicial
st.set_page_config(page_title="Facturación PRO", layout="wide", page_icon="💰")

# Estilos CSS mejorados
st.markdown("""
<style>
    .stApp { background-color: #0b1220; }
    h1, h2, h3 { color: #e6eefc; font-family: 'Inter', sans-serif; }
    .card-blue { background: linear-gradient(135deg, #102a43, #0f1f33); border: 1px solid #1f4e79; border-radius: 14px; padding: 20px; margin-bottom: 10px; }
    .card-green { background: linear-gradient(135deg, #0f2a1f, #0c1f18); border: 1px solid #2a7f62; border-radius: 14px; padding: 20px; margin-bottom: 10px; }
    .card-total { background: linear-gradient(135deg, #2a1f3d, #1b1328); border: 1px solid #7a5cff; border-radius: 14px; padding: 15px; text-align: center; font-size: 22px; color: #cdbfff; margin: 15px 0; font-weight: bold; }
    [data-testid="stMetric"] { background: #111a2b; border: 1px solid #1f2a44; border-radius: 12px; padding: 10px; }
</style>
""", unsafe_allow_html=True)

# ─── CONEXIÓN GOOGLE SHEETS ───
@st.cache_resource
def get_gsheet_client():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(dict(st.secrets["gcp_service_account"]), scope)
    return gspread.authorize(creds)

try:
    client = get_gsheet_client()
    spreadsheet = client.open_by_url("https://docs.google.com/spreadsheets/d/1JgpD7qiclpmTuLoHDWCIWdtJ5DPdZKeURFwkXv3_e7U/edit")
    sheet = spreadsheet.worksheet("Hoja 1")
except Exception as e:
    st.error(f"Error de conexión: {e}")
    st.stop()

# ─── LÓGICA DE CÁLCULO ───
def safe_int(value):
    try: return int(float(value)) if value not in [None, ""] else 0
    except: return 0

def calc_colmenar(fg, lg, fpsi, lpsi):
    fijo = 800
    variable = max(0, (fg - 1404 - lg) * 0.35 + (fpsi - 1428 - lpsi) * 0.30)
    bruto = fijo + variable
    return bruto, bruto * 0.70

def calc_valdemoro(fpsi_v, lpsi_v):
    fijo = 800
    var = max((fpsi_v - lpsi_v - 3730), 0) * 0.30
    bruto = fijo + var
    return bruto, bruto * 0.70

def calcular_irpf(base):
    tramos = [(12450, 0.19), (20200, 0.24), (35200, 0.30), (60000, 0.37), (float('inf'), 0.45)]
    impuesto, anterior = 0, 0
    for limite, tipo in tramos:
        if base > anterior:
            tramo = min(base, limite) - anterior
            impuesto += tramo * tipo
            anterior = limite
    return impuesto

# ─── INTERFAZ PRINCIPAL ───
st.title("💰 Facturación Clínica PRO")

year = st.selectbox("📅 Seleccionar Año Fiscal", list(range(2024, datetime.now().year + 3)), index=0)

# Carga de datos
try:
    data_sheet = sheet.get_all_records()
except:
    data_sheet = []

datos_por_mes = {str(row.get("Mes", "")): row for row in data_sheet if str(row.get("Año", "")) == str(year)}

meses = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]

# Variables acumuladoras
total_ingresos, total_retenido = 0.0, 0.0
netos_grafica = []
datos_para_guardar = []

# Uso de Tabs para mejorar la navegación
tab_fact, tab_stats = st.tabs(["📝 Entrada de Datos", "📊 Resumen Anual"])

with tab_fact:
    for mes in meses:
        with st.expander(f"📅 {mes}", expanded=(mes == meses[datetime.now().month - 1])):
            d = datos_por_mes.get(mes, {})
            col1, col2 = st.columns(2)

            with col1:
                st.markdown('<div class="card-blue">', unsafe_allow_html=True)
                st.markdown("#### 🔵 Colmenar")
                fg = st.number_input("Fact General €", value=safe_int(d.get("FG")), key=f"fg_{mes}")
                lg = st.number_input("Lab General €", value=safe_int(d.get("LG")), key=f"lg_{mes}")
                fpsi = st.number_input("Fact PSI €", value=safe_int(d.get("FPSI")), key=f"fpsi_{mes}")
                lpsi = st.number_input("Lab PSI €", value=safe_int(d.get("LPSI")), key=f"lpsi_{mes}")
                bruto_c, neto_c = calc_colmenar(fg, lg, fpsi, lpsi)
                st.metric("Neto Colmenar", f"{round(neto_c)} €")
                st.markdown('</div>', unsafe_allow_html=True)

            with col2:
                st.markdown('<div class="card-green">', unsafe_allow_html=True)
                st.markdown("#### 🟢 Valdemoro")
                fpsi_v = st.number_input("Fact PSI V €", value=safe_int(d.get("FPSI_V")), key=f"fv_{mes}")
                lpsi_v = st.number_input("Lab PSI V €", value=safe_int(d.get("LPSI_V")), key=f"lv_{mes}")
                bruto_v, neto_v = calc_valdemoro(fpsi_v, lpsi_v)
                st.metric("Neto Valdemoro", f"{round(neto_v)} €")
                st.markdown('</div>', unsafe_allow_html=True)

            total_mes = round(neto_c + neto_v)
            st.markdown(f'<div class="card-total">💰 TOTAL {mes.upper()}: {total_mes} €</div>', unsafe_allow_html=True)
            
            # Acumular datos
            total_ingresos += (bruto_c + bruto_v)
            total_retenido += (bruto_c + bruto_v) * 0.30
            netos_grafica.append(total_mes)
            datos_para_guardar.append([year, mes, fg, lg, fpsi, lpsi, fpsi_v, lpsi_v, total_mes])

    if st.button("💾 Guardar Todo en la Nube", use_container_width=True):
        with st.spinner("Sincronizando con Google Sheets..."):
            # Lógica de guardado optimizada
            current_data = sheet.get_all_records()
            for row_data in datos_para_guardar:
                # Buscar si ya existe la fila para el año/mes
                found_idx = next((i + 2 for i, r in enumerate(current_data) if str(r.get("Año")) == str(year) and r.get("Mes") == row_data[1]), None)
                if found_idx:
                    sheet.update(f"A{found_idx}:I{found_idx}", [row_data])
                else:
                    sheet.append_row(row_data)
            st.success("¡Datos actualizados correctamente! 🔥")

with tab_stats:
    st.header("📊 Análisis Fiscal y Rendimiento")
    
    # Cálculos Hacienda
    base_imponible = max(total_ingresos - 500 - 2000 - 5550, 0)
    irpf_real = calcular_irpf(base_imponible)
    diferencia = total_retenido - irpf_real

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Ingresos Brutos", f"{round(total_ingresos)}€")
    c2.metric("Retención (30%)", f"{round(total_retenido)}€")
    c3.metric("Base Imponible", f"{round(base_imponible)}€")
    c4.metric("IRPF Teórico", f"{round(irpf_real)}€")

    if diferencia > 0:
        st.success(f"### 🟢 Hacienda te devuelve: **{round(diferencia)} €**")
    else:
        st.error(f"### 🔴 Resultado de la declaración: **{round(abs(diferencia))} € a pagar**")

    st.divider()
    
    # Gráfica de evolución
    st.subheader("📈 Evolución de Ingresos Netos")
    df_plot = pd.DataFrame({"Mes": meses, "Neto (€)": netos_grafica})
    st.line_chart(df_plot.set_index("Mes"), color="#7a5cff")
