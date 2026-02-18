import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import google.generativeai as genai

# --- CONFIGURACIÓN CRÍTICA ---
# Pega tu API KEY aquí abajo entre las comillas
API_KEY = "AIzaSyDDARUGlDLNqKy_brhfc-zWv4u1rM9mKls"  
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

st.set_page_config(page_title="ZenTrader Sentinel AI", layout="wide", page_icon="🧘")

# Estilos para celular y PC
st.markdown("""
    <style>
    .stMetric { background-color: rgba(255,255,255,0.05); border-radius: 10px; padding: 10px !important; }
    </style>
    """, unsafe_allow_html=True)

# --- FUNCIÓN DE 5 DECIMALES ---
def formato_exacto(simbolo, precio):
    if precio is None: return "0.00"
    s = str(simbolo).upper()
    # Lista de pares que necesitan 5 decimales
    if any(x in s for x in ["EURUSD", "GBPUSD", "AUDUSD", "EUR", "GBP"]): 
        return f"{precio:.5f}"
    return f"{precio:,.2f}"

# --- OBTENER DATOS ---
def obtener_datos(ticker):
    try:
        data = yf.download(ticker, period="1mo", interval="1h", progress=False)
        if isinstance(data.columns, pd.MultiIndex): data.columns = data.columns.droplevel(1)
        data = data.reset_index()
        
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
        
        return data
    except:
        return pd.DataFrame()

# --- INTERFAZ PRINCIPAL ---
st.title("🧘 ZenTrader: La Biblia del Trader")

# Barra lateral
with st.sidebar:
    st.header("Control de Mando")
    zen_score = st.slider("Nivel de Estrés (Biofeedback)", 0, 100, 50, help="0 = Zen, 100 = Pánico")
    st.info("💡 Consejo: Si tu estrés es alto, el bot te recomendará no operar.")

# Selector de Activos
col1, col2 = st.columns([1, 3])
with col1:
    opcion = st.selectbox("Selecciona Activo", ["EUR/USD (Forex)", "Bitcoin (Cripto)", "Oro (Commodity)"])
    mapa = {"EUR/USD (Forex)": "EURUSD=X", "Bitcoin (Cripto)": "BTC-USD", "Oro (Commodity)": "GC=F"}
    ticker = mapa[opcion]

data = obtener_datos(ticker)

if not data.empty:
    ultimo = data.iloc[-1]
    precio_str = formato_exacto(ticker, ultimo['Close'])

    # ZONAS DE FRANCOTIRADOR (Con 5 decimales)
    st.subheader(f"🎯 Análisis de {opcion}")
    kpi1, kpi2, kpi3 = st.columns(3)
    kpi1.metric("PRECIO ACTUAL", precio_str)
    kpi2.metric("RSI (Fuerza)", f"{ultimo['RSI']:.2f}")
    kpi3.metric("Banda Superior", formato_exacto(ticker, ultimo['Upper']))

    # GRÁFICO (Bandas siempre visibles)
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.7, 0.3], vertical_spacing=0.05)
    
    # Velas
    fig.add_trace(go.Candlestick(x=data['Date'], open=data['Open'], high=data['High'], low=data['Low'], close=data['Close'], name="Precio"), row=1, col=1)
    
    # Bandas de Bollinger (Sombreadas)
    fig.add_trace(go.Scatter(x=data['Date'], y=data['Upper'], line=dict(color='rgba(0, 255, 255, 0.3)'), name="Banda Sup"), row=1, col=1)
    fig.add_trace(go.Scatter(x=data['Date'], y=data['Lower'], line=dict(color='rgba(0, 255, 255, 0.3)'), fill='tonexty', name="Banda Inf"), row=1, col=1)
    
    # RSI
    fig.add_trace(go.Scatter(x=data['Date'], y=data['RSI'], line=dict(color='#A020F0'), name="RSI"), row=2, col=1)
    fig.add_hline(y=70, line_dash="dot", row=2, col=1)
    fig.add_hline(y=30, line_dash="dot", row=2, col=1)
    
    fig.update_layout(template="plotly_dark", xaxis_rangeslider_visible=False, height=600)
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    # CHATBOT GEMINI INTEGRADO
    st.subheader("🤖 Mentor IA (Análisis en Tiempo Real)")
    
    # Historial de chat
    if "mensajes" not in st.session_state:
        st.session_state.mensajes = []

    for m in st.session_state.mensajes:
        with st.chat_message(m["role"]): st.markdown(m["content"])

    # Input del usuario
    if pregunta := st.chat_input("Pregúntame sobre el gráfico..."):
        st.session_state.mensajes.append({"role": "user", "content": pregunta})
        with st.chat_message("user"): st.markdown(pregunta)
        
        with st.chat_message("assistant"):
            try:
                # Prompt con contexto real del mercado
                contexto = f"""
                Eres un trader experto. 
                El usuario está viendo {opcion}.
                Precio: {precio_str}.
                RSI: {ultimo['RSI']:.2f}.
                Su nivel de estrés reportado es: {zen_score}/100.
                
                Si el estrés es mayor a 70, recomiéndale cerrar la pantalla.
                Si el RSI está sobre 70 o bajo 30, advierte sobre reversión.
                Responde breve y directo a la pregunta: "{pregunta}"
                """
                respuesta = model.generate_content(contexto).text
                st.markdown(respuesta)
                st.session_state.mensajes.append({"role": "assistant", "content": respuesta})
            except Exception as e:
                st.error("Error de conexión con la IA. Revisa tu API KEY.")
