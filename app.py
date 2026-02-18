import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import google.generativeai as genai

# ==========================================
# 🔑 ZONA DE LLAVES (API KEY)
# ==========================================
# BORRA EL TEXTO ENTRE COMILLAS Y PEGA TU CLAVE:
API_KEY = "AIzaSyDDARUGlDLNqKy_brhfc-zWv4u1rM9mKls"  
try:
    genai.configure(api_key=API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
    st.error(f"Error configurando la IA: {e}")

# Configuración de página
st.set_page_config(page_title="ZenTrader Pro", layout="wide", page_icon="🧘")

# CSS CORREGIDO (Para que se vea bien en celular)
st.markdown("""
    <style>
    /* Ajusta el tamaño de los números para que no se encimen */
    div[data-testid="stMetricValue"] {
        font-size: 20px !important;
    }
    /* Ajuste para móviles */
    @media (max-width: 640px) {
        .stPlotlyChart { height: 400px !important; }
        h1 { font-size: 1.5rem !important; }
    }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 🧠 CEREBRO MATEMÁTICO
# ==========================================

# 1. Función de 5 Decimales
def estilo_preciso(simbolo, precio):
    if precio is None: return "0.00"
    s = str(simbolo).upper()
    # Si es Forex (Euro, Libra, Aud), usa 5 decimales
    if any(x in s for x in ["EURUSD", "GBPUSD", "AUDUSD", "EUR", "GBP"]): 
        return f"{precio:.5f}"
    # Si es Yen u otros, 3 decimales
    if "JPY" in s: return f"{precio:.3f}"
    # Bitcoin y el resto, 2 decimales
    return f"{precio:,.2f}"

# 2. Obtener Datos (CORREGIDO EL TIEMPO)
def obtener_datos(ticker):
    try:
        # Descargar datos
        data = yf.download(ticker, period="1mo", interval="1h", progress=False)
        
        # Corrección para yfinance (elimina multi-índices)
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.droplevel(1)
            
        data = data.reset_index() 
        
        # --- CORRECCIÓN FECHAS ---
        # Detectamos automáticamente la columna de fecha
        col_fecha = data.columns[0] 
        
        # Indicadores Técnicos
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
    except Exception as e:
        return pd.DataFrame(), None

# ==========================================
# 🖥️ INTERFAZ DE USUARIO
# ==========================================
st.title("🛡️ ZenTrader: Francotirador")

# Sidebar
with st.sidebar:
    st.header("Radar de Mercado")
    opcion = st.selectbox("Activo", ["Bitcoin", "EUR/USD", "Oro", "GBP/USD"])
    mapa = {"EUR/USD": "EURUSD=X", "Bitcoin": "BTC-USD", "Oro": "GC=F", "GBP/USD": "GBPUSD=X"}
    ticker = mapa[opcion]
    
    st.divider()
    zen_score = st.slider("Nivel de Estrés", 0, 100, 50)

# Cargar Datos
data, nombre_fecha = obtener_datos(ticker)

if not data.empty and nombre_fecha:
    ultimo = data.iloc[-1]
    precio_actual = ultimo['Close']
    
    # --- ZONAS DE FRANCOTIRADOR ---
    st.subheader(f"🎯 Plan para {opcion}")
    
    # Precios objetivo (Ejemplo básico de TP/SL)
    tp = precio_actual * 1.002
    sl = precio_actual * 0.998
    
    c1, c2, c3 = st.columns(3)
    c1.metric("ENTRADA", estilo_preciso(ticker, precio_actual))
    c2.metric("TAKE PROFIT", estilo_preciso(ticker, tp))
    c3.metric("STOP LOSS", estilo_preciso(ticker, sl))

    # --- GRÁFICO TÉCNICO ---
    st.markdown("---")
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.7, 0.3], vertical_spacing=0.05)
    
    # Usamos la columna de fecha real para el eje X
    eje_x = data[nombre_fecha]
    
    # Velas
    fig.add_trace(go.Candlestick(x=eje_x, open=data['Open'], high=data['High'], low=data['Low'], close=data['Close'], name="Precio"), row=1, col=1)
    
    # Bandas (Sombreadas)
    fig.add_trace(go.Scatter(x=eje_x, y=data['Upper'], line=dict(color='rgba(0, 191, 255, 0.3)'), name="Banda Sup"), row=1, col=1)
    fig.add_trace(go.Scatter(x=eje_x, y=data['Lower'], line=dict(color='rgba(0, 191, 255, 0.3)'), fill='tonexty', name="Banda Inf"), row=1, col=1)
    
    # RSI
    fig.add_trace(go.Scatter(x=eje_x, y=data['RSI'], line=dict(color='#9b59b6'), name="RSI"), row=2, col=1)
    fig.add_hline(y=70, line_dash="dot", row=2, col=1)
    fig.add_hline(y=30, line_dash="dot", row=2, col=1)
    
    fig.update_layout(template="plotly_dark", xaxis_rangeslider_visible=False, height=500, margin=dict(l=10, r=10, t=10, b=10))
    st.plotly_chart(fig, use_container_width=True)

else:
    st.warning("Cargando datos... Si demora, revisa tu conexión.")

# ==========================================
# 🤖 CHATBOT MENTOR IA
# ==========================================
st.divider()
st.subheader("💬 Mentor IA")

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]): st.markdown(msg["content"])

if prompt := st.chat_input("Consulta sobre el mercado..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)
    
    with st.chat_message("assistant"):
        try:
            # Contexto para que la IA sepa qué estás viendo
            contexto = f"""
            Eres un trader experto. Analiza el activo {opcion}.
            Precio Actual: {estilo_preciso(ticker, precio_actual)}.
            RSI: {ultimo['RSI']:.2f}.
            El usuario reporta un estrés de {zen_score}%.
            Responde breve y directo a la pregunta: "{prompt}"
            """
            response = model.generate_content(contexto)
            st.markdown(response.text)
            st.session_state.messages.append({"role": "assistant", "content": response.text})
        except Exception as e:
            st.error("Error de conexión con la IA. Verifica tu API KEY.")
