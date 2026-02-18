import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import google.generativeai as genai

# --- CONFIGURACIÓN DE IA ---
# Usa siempre comillas para la clave
API_KEY = "AIzaSyDDARUGlDLNqKy_brhfc-zWv4u1rM9mKls" 
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

st.set_page_config(page_title="ZenTrader Sentinel AI", layout="wide")

# CSS para que no tengan que doblar el celular
st.markdown("""
    <style>
    @media (max-width: 640px) {
        .stMetric { padding: 2px !important; }
        .stPlotlyChart { height: 350px !important; }
        h1 { font-size: 1.2rem !important; }
    }
    </style>
    """, unsafe_allow_html=True)

# Función Maestra de Decimales (Afecta a TODO)
def f_p(simbolo, precio):
    if precio is None: return "0.00"
    s = str(simbolo).upper()
    if any(x in s for x in ["EURUSD", "GBPUSD", "AUDUSD", "=X"]): 
        return f"{precio:.5f}" # Aquí forzamos los 5 decimales
    return f"{precio:,.2f}"

# --- MOTOR DE DATOS Y GRÁFICOS ---
def get_data(ticker):
    data = yf.download(ticker, period="1mo", interval="1h", progress=False)
    if isinstance(data.columns, pd.MultiIndex): data.columns = data.columns.droplevel(1)
    data = data.reset_index()
    
    # Cálculos Técnicos
    data['MA20'] = data['Close'].rolling(window=20).mean()
    data['STD'] = data['Close'].rolling(window=20).std()
    data['Upper'] = data['MA20'] + (data['STD'] * 2)
    data['Lower'] = data['MA20'] - (data['STD'] * 2)
    
    # RSI
    delta = data['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    data['RSI'] = 100 - (100 / (1 + (gain / loss)))
    return data

# --- INTERFAZ ---
st.title("🛡️ ZenTrader Sentinel AI")

# Sidebar
with st.sidebar:
    st.header("Biofeedback")
    score = st.slider("Zen Score", 0, 100, 70)

# Selector
activos = {"Euro/Dólar": "EURUSD=X", "Bitcoin": "BTC-USD", "Oro": "GC=F"}
seleccion = st.selectbox("Mercado", list(activos.keys()))
ticker = activos[seleccion]

data = get_data(ticker)
ultimo = data.iloc[-1]

# 1. ZONAS DE FRANCOTIRADOR (CORREGIDO A 5 DECIMALES)
st.subheader("🎯 Zonas de Francotirador")
c1, c2, c3 = st.columns(3)
c1.metric("LA OFERTA", f_p(ticker, ultimo['Close'] * 0.999))
c2.metric("EL TECHO", f_p(ticker, ultimo['Close'] * 1.001))
c3.metric("PROTECCIÓN", f_p(ticker, ultimo['Close'] * 0.998))

# 2. GRÁFICO (CON BOLLINGER SIEMPRE VISIBLES)
fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.7, 0.3], vertical_spacing=0.05)
fig.add_trace(go.Candlestick(x=data.index, open=data['Open'], high=data['High'], low=data['Low'], close=data['Close'], name="Precio"), row=1, col=1)

# Dibujar Bandas
fig.add_trace(go.Scatter(x=data.index, y=data['Upper'], line=dict(color='rgba(173, 216, 230, 0.2)'), name="Bollinger Superior"), row=1, col=1)
fig.add_trace(go.Scatter(x=data.index, y=data['Lower'], line=dict(color='rgba(173, 216, 230, 0.2)'), fill='tonexty', name="Bollinger Inferior"), row=1, col=1)

# RSI
fig.add_trace(go.Scatter(x=data.index, y=data['RSI'], line=dict(color='purple'), name="RSI"), row=2, col=1)
fig.update_layout(template="plotly_dark", xaxis_rangeslider_visible=False, height=500)
st.plotly_chart(fig, use_container_width=True)

# 3. CHATBOT INTERACTIVO
st.divider()
st.subheader("💬 Mentor Crítico Gemini")
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

for m in st.session_state.chat_history:
    with st.chat_message(m["role"]): st.markdown(m["content"])

if prompt := st.chat_input("¿Qué opinas de este precio?"):
    st.session_state.chat_history.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)
    
    with st.chat_message("assistant"):
        context = f"Analiza: {seleccion} a {ultimo['Close']:.5f}. RSI: {ultimo['RSI']:.2f}. ZenScore: {score}%."
        response = model.generate_content(context + "\nPregunta: " + prompt)
        st.markdown(response.text)
        st.session_state.chat_history.append({"role": "assistant", "content": response.text})

