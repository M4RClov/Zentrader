import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import google.generativeai as genai

# ==========================================
# 🔑 CONFIGURACIÓN Y CLAVES
# ==========================================
st.set_page_config(page_title="ZenTrader Master", layout="wide", page_icon="🧘")

# --- PEGA TU API KEY AQUÍ ---
API_KEY = "AIzaSyDDARUGlDLNqKy_brhfc-zWv4u1rM9mKls"  

try:
    genai.configure(api_key=API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')
    ai_active = True
except:
    ai_active = False

# ==========================================
# 🎨 ESTILOS (CSS PRO)
# ==========================================
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    
    /* Tarjetas de Métricas */
    div[data-testid="stMetric"] {
        background-color: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 8px;
        padding: 10px;
    }
    
    /* Ajuste de textos */
    div[data-testid="stMetricValue"] { font-size: 18px !important; }
    div[data-testid="stMetricLabel"] { font-size: 14px !important; color: #b0bec5; }
    
    /* Celular */
    @media (max-width: 640px) {
        .stPlotlyChart { height: 400px !important; }
        h1 { font-size: 1.5rem !important; }
    }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 🧠 FUNCIONES DEL NÚCLEO
# ==========================================

def estilo_preciso(simbolo, precio):
    """Formato inteligente de decimales"""
    if precio is None: return "0.00"
    s = str(simbolo).upper()
    if any(x in s for x in ["EURUSD", "GBPUSD", "AUDUSD", "EUR", "GBP"]): return f"{precio:.5f}"
    if "JPY" in s: return f"{precio:.3f}"
    if any(x in s for x in ["BTC", "ETH", "XAU"]): return f"{precio:,.2f}"
    return f"{precio:,.2f}"

def obtener_datos(ticker):
    """Descarga y calcula indicadores técnicos"""
    try:
        data = yf.download(ticker, period="1mo", interval="1h", progress=False)
        if isinstance(data.columns, pd.MultiIndex): data.columns = data.columns.droplevel(1)
        data = data.reset_index()
        
        # Detectar fecha
        col_fecha = data.columns[0]
        
        # Indicadores
        data['MA20'] = data['Close'].rolling(window=20).mean()
        data['STD'] = data['Close'].rolling(window=20).std()
        data['Upper'] = data['MA20'] + (data['STD'] * 2)
        data['Lower'] = data['MA20'] - (data['STD'] * 2)
        
        # RSI
        delta = data['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        data['RSI'] = 100 - (100 / (1 + (gain / loss)))
        
        return data, col_fecha
    except:
        return pd.DataFrame(), None

def obtener_precios_live():
    """Obtiene precios rápidos para la cinta superior"""
    lista = {
        "Bitcoin": "BTC-USD", "Ethereum": "ETH-USD", 
        "EUR/USD": "EURUSD=X", "Oro": "GC=F",
        "S&P 500": "^GSPC", "Nvidia": "NVDA",
        "Dólar Index": "DX-Y.NYB", "GBP/USD": "GBPUSD=X"
    }
    datos = {}
    try:
        df = yf.download(list(lista.values()), period="1d", progress=False)['Close']
        for nombre, ticker in lista.items():
            try:
                # Manejo de yfinance reciente
                if isinstance(df, pd.DataFrame):
                    if isinstance(df.columns, pd.MultiIndex):
                        val = df[ticker].iloc[-1]
                    else:
                        # Intento de acceso directo si la estructura varía
                         val = df.iloc[-1][ticker] if ticker in df.columns else 0
                else:
                     val = df.iloc[-1]
                datos[nombre] = val
            except:
                datos[nombre] = 0.0
    except:
        pass
    return datos, lista

# ==========================================
# 🖥️ INTERFAZ PRINCIPAL
# ==========================================

# 1. SIDEBAR (Biofeedback)
with st.sidebar:
    st.header("🧠 Biofeedback")
    st.info("El trading es 90% mental.")
    zen_score = st.slider("Nivel de Calma (1-100)", 0, 100, 75)
    
    if zen_score < 50:
        st.error("⚠️ RIESGO ALTO: No operes.")
    else:
        st.success("✅ ESTADO ÓPTIMO")
    
    st.divider()
    st.write("Configuración:")
    opcion_activo = st.selectbox("Activo Principal", ["Bitcoin", "EUR/USD", "Oro", "GBP/USD", "Nvidia"])

# 2. CINTA DE PRECIOS (RADAR GLOBAL)
st.title("🛡️ ZenTrader: Master Dashboard")
st.markdown("### 📡 Radar de Mercado Global")

precios_live, mapa_tickers = obtener_precios_live()

# Mostramos 8 activos en 2 filas de 4 columnas
if precios_live:
    claves = list(precios_live.keys())
    
    # Fila 1
    c1, c2, c3, c4 = st.columns(4)
    with c1: st.metric("Bitcoin", estilo_preciso("BTC", precios_live["Bitcoin"]))
    with c2: st.metric("Ethereum", estilo_preciso("ETH", precios_live["Ethereum"]))
    with c3: st.metric("Oro (XAU)", estilo_preciso("XAU", precios_live["Oro"]))
    with c4: st.metric("S&P 500", f"{precios_live['S&P 500']:,.2f}")
    
    # Fila 2
    c5, c6, c7, c8 = st.columns(4)
    with c5: st.metric("EUR/USD", estilo_preciso("EURUSD", precios_live["EUR/USD"]))
    with c6: st.metric("GBP/USD", estilo_preciso("GBPUSD", precios_live["GBP/USD"]))
    with c7: st.metric("Nvidia", f"{precios_live['Nvidia']:,.2f}")
    with c8: st.metric("Dólar Index", f"{precios_live['Dólar Index']:,.3f}")

st.markdown("---")

# 3. ANÁLISIS DETALLADO (SNIPER)
ticker_actual = mapa_tickers.get(opcion_activo, "BTC-USD")
data, col_fecha = obtener_datos(ticker_actual)

if not data.empty and col_fecha:
    ultimo = data.iloc[-1]
    precio = ultimo['Close']
    
    # Zonas Francotirador
    st.subheader(f"🎯 Plan de Batalla: {opcion_activo}")
    
    tp = precio * 1.0025 # +0.25%
    sl = precio * 0.9975 # -0.25%
    
    k1, k2, k3 = st.columns(3)
    k1.metric("ENTRADA (Precio)", estilo_preciso(ticker_actual, precio))
    k2.metric("TAKE PROFIT (+0.25%)", estilo_preciso(ticker_actual, tp))
    k3.metric("STOP LOSS (-0.25%)", estilo_preciso(ticker_actual, sl))
    
    # Gráfico
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.7, 0.3], vertical_spacing=0.05)
    eje_x = data[col_fecha]
    
    # Velas
    fig.add_trace(go.Candlestick(x=eje_x, open=data['Open'], high=data['High'], low=data['Low'], close=data['Close'], name="Precio"), row=1, col=1)
    
    # Bandas
    fig.add_trace(go.Scatter(x=eje_x, y=data['Upper'], line=dict(color='rgba(0, 255, 255, 0.3)'), name="Banda Sup"), row=1, col=1)
    fig.add_trace(go.Scatter(x=eje_x, y=data['Lower'], line=dict(color='rgba(0, 255, 255, 0.3)'), fill='tonexty', name="Banda Inf"), row=1, col=1)
    
    # RSI
    fig.add_trace(go.Scatter(x=eje_x, y=data['RSI'], line=dict(color='#ab47bc'), name="RSI"), row=2, col=1)
    fig.add_hline(y=70, line_dash="dot", row=2, col=1)
    fig.add_hline(y=30, line_dash="dot", row=2, col=1)
    
    fig.update_layout(template="plotly_dark", xaxis_rangeslider_visible=False, height=600, margin=dict(l=10, r=10, t=10, b=10))
    st.plotly_chart(fig, use_container_width=True)

# 4. CHATBOT GEMINI (Al final)
st.divider()
st.subheader("🤖 Mentor IA (Gemini Live)")

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

for msg in st.session_state.chat_history:
    with st.chat_message(msg["role"]): st.markdown(msg["content"])

if prompt := st.chat_input(f"Pregunta sobre {opcion_activo}..."):
    st.session_state.chat_history.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)
    
    if ai_active:
        with st.chat_message("assistant"):
            try:
                contexto = f"""
                Eres un trader institucional experto. 
                Activo: {opcion_activo}. Precio: {estilo_preciso(ticker_actual, precio)}.
                RSI: {ultimo['RSI']:.2f}. Zen Score usuario: {zen_score}%.
                Si Zen Score < 50, recomienda no operar.
                Responde breve y táctico.
                """
                res = model.generate_content(contexto + "\nPregunta: " + prompt)
                st.markdown(res.text)
                st.session_state.chat_history.append({"role": "assistant", "content": res.text})
            except Exception as e:
                st.error(f"Error IA: {e}")
    else:
        st.error("⚠️ API Key no configurada o inválida.")

