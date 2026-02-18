import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import google.generativeai as genai
import feedparser
from bs4 import BeautifulSoup
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import pytz
from datetime import datetime

# ==========================================
# ⚙️ CONFIGURACIÓN INICIAL
# ==========================================
st.set_page_config(page_title="ZenTrader Sentinel", layout="wide", page_icon="🧘")

# --- 🔑 TU API KEY AQUÍ ---
API_KEY = "AIzaSyDDARUGlDLNqKy_brhfc-zWv4u1rM9mKls"  

# Configurar IA
ai_active = False
if API_KEY != "AIzaSyDDARUGlDLNqKy_brhfc-zWv4u1rM9mKls":
    try:
        genai.configure(api_key=API_KEY)
        model = genai.GenerativeModel('gemini-1.5-flash')
        ai_active = True
    except:
        pass

# Inicializar VADER
analyzer = SentimentIntensityAnalyzer()

# ==========================================
# 🎨 ESTÉTICA "CYBER-ZEN" (CSS PRO)
# ==========================================
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;700&display=swap');
    
    /* FONDO Y TEXTO GLOBAL */
    .main { background-color: #0e1117; color: #e0e0e0; font-family: 'Poppins', sans-serif; }
    
    /* TARJETAS DE CRISTAL (Glassmorphism) */
    div[data-testid="stMetric"], .glass-card, .news-card, .wiki-card {
        background-color: rgba(255, 255, 255, 0.03) !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        border-radius: 12px;
        padding: 15px;
        backdrop-filter: blur(10px);
        box-shadow: 0 4px 6px rgba(0,0,0,0.2);
    }
    
    /* LOGO ZEN-TRADER */
    .main-logo { font-size: 3rem; font-weight: 700; text-align: center; margin-bottom: 20px; }
    .zen-text { color: #26a69a; }
    .trader-text { color: #ffb74d; }
    
    /* RELOJES */
    .clock-box { text-align: center; border-right: 1px solid #333; }
    .clock-time { font-family: 'Courier New', monospace; font-size: 2em; font-weight: bold; color: #e0e0e0; }
    .clock-city { font-size: 0.8em; color: #90a4ae; text-transform: uppercase; letter-spacing: 2px; }
    
    /* NOTICIAS */
    .news-title { font-weight: 600; color: #fff; text-decoration: none; font-size: 1.1em; }
    .news-source { font-size: 0.75em; color: #aaa; text-transform: uppercase; }
    
    /* AJUSTE MOVIL */
    @media (max-width: 640px) {
        .stPlotlyChart { height: 400px !important; }
        .clock-box { border-right: none; border-bottom: 1px solid #333; padding-bottom: 10px; margin-bottom: 10px; }
    }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 🧠 FUNCIONES DEL NÚCLEO
# ==========================================

def estilo_preciso(simbolo, precio):
    if precio is None or pd.isna(precio): return "0.00"
    s = str(simbolo).upper()
    if any(x in s for x in ["EURUSD", "GBPUSD", "EUR", "GBP"]): return f"{precio:.5f}"
    if "JPY" in s: return f"{precio:.3f}"
    if any(x in s for x in ["BTC", "ETH", "XAU"]): return f"{precio:,.2f}"
    return f"{precio:,.2f}"

@st.cache_data(ttl=60)
def obtener_precios_live():
    tickers = {
        "Bitcoin": "BTC-USD", "Ethereum": "ETH-USD", 
        "S&P 500": "^GSPC", "Nvidia": "NVDA", "Oro": "GC=F",
        "EUR/USD": "EURUSD=X", "GBP/USD": "GBPUSD=X", "DXY": "DX-Y.NYB"
    }
    data = {}
    for nombre, simbolo in tickers.items():
        try:
            df = yf.download(simbolo, period="2d", progress=False)
            if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.droplevel(1)
            if not df.empty:
                precio = df['Close'].iloc[-1]
                previo = df['Close'].iloc[-2] if len(df) > 1 else df['Open'].iloc[-1]
                cambio = ((precio - previo) / previo) * 100
                data[nombre] = (precio, cambio)
            else:
                data[nombre] = (None, 0.0)
        except:
            data[nombre] = (None, 0.0)
    return data, tickers

def get_chart_data(ticker):
    try:
        df = yf.download(ticker, period="1mo", interval="1h", progress=False)
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.droplevel(1)
        df = df.reset_index()
        date_col = df.columns[0]
        
        df['MA20'] = df['Close'].rolling(window=20).mean()
        std = df['Close'].rolling(window=20).std()
        df['Upper'] = df['MA20'] + (std * 2)
        df['Lower'] = df['MA20'] - (std * 2)
        
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))
        return df, date_col
    except:
        return pd.DataFrame(), None

def clean_html(text):
    return BeautifulSoup(text, "html.parser").get_text()

def fetch_news():
    url = "https://es.investing.com/rss/news.rss"
    feeds = feedparser.parse(url)
    news_items = []
    for entry in feeds.entries[:6]:
        title = clean_html(entry.title)
        sentiment = analyzer.polarity_scores(title)['compound']
        color = "#00e676" if sentiment > 0.05 else "#ff1744" if sentiment < -0.05 else "#b0bec5" # Verde/Rojo/Gris
        news_items.append({"title": title, "link": entry.link, "color": color, "source": "Investing"})
    return news_items

# ==========================================
# 🖥️ UI PRINCIPAL
# ==========================================

# 1. LOGO Y RELOJES
st.markdown('<div class="main-logo"><span class="zen-text">ZEN</span><span class="trader-text">TRADER</span></div>', unsafe_allow_html=True)

# Relojes Mundiales (Estilo Sentinel)
c1, c2, c3 = st.columns(3)
tzs = {"NY": "America/New_York", "LDN": "Europe/London", "TOK": "Asia/Tokyo"}

def show_clock(col, city, tz):
    time = datetime.now(pytz.timezone(tz)).strftime('%H:%M')
    col.markdown(f"""
    <div class="glass-card" style="text-align: center;">
        <div class="clock-city">{city}</div>
        <div class="clock-time">{time}</div>
    </div>
    """, unsafe_allow_html=True)

show_clock(c1, "WALL STREET", tzs["NY"])
show_clock(c2, "LONDRES", tzs["LDN"])
show_clock(c3, "TOKIO", tzs["TOK"])

st.markdown("---")

# 2. SIDEBAR (BIOFEEDBACK & CONTROL)
with st.sidebar:
    st.header("🛡️ Protocolo Biofeedback")
    
    # Sliders visuales
    zen_score = st.slider("Estado Mental (1-100)", 0, 100, 85)
    sueno = st.slider("Horas de Sueño", 0, 12, 7)
    
    if zen_score >= 70:
        st.success(f"✅ SISTEMA APROBADO ({zen_score}%)")
    elif zen_score >= 50:
        st.warning(f"⚠️ PRECAUCIÓN ({zen_score}%)")
    else:
        st.error(f"🚫 BLOQUEO DE SEGURIDAD ({zen_score}%)")
    
    st.divider()
    active_selection = st.selectbox("ACTIVO PRINCIPAL", ["Bitcoin", "EUR/USD", "Oro", "S&P 500", "Nvidia"])
    
    st.info("💡 RECUERDA: El 90% del trading es esperar. El 10% es ejecución.")

# 3. CINTA DE PRECIOS LIVE
market_data, ticker_map = obtener_precios_live()
st.subheader("📡 Inteligencia de Mercado")

# Fila 1
m1, m2, m3, m4 = st.columns(4)
def card(col, label, key):
    val, chg = market_data.get(key, (None, 0.0))
    if val: 
        color = "normal"
        if chg > 0: color = "off" # Streamlit metric handles colors auto
        col.metric(label, estilo_preciso(key, val), f"{chg:.2f}%")
    else:
        col.metric(label, "Cargando...", None)

card(m1, "Bitcoin", "Bitcoin")
card(m2, "Ethereum", "Ethereum")
card(m3, "S&P 500", "S&P 500")
card(m4, "Nvidia", "Nvidia")

# Fila 2
m5, m6, m7, m8 = st.columns(4)
card(m5, "EUR/USD", "EUR/USD")
card(m6, "Oro (XAU)", "Oro")
card(m7, "GBP/USD", "GBP/USD")
card(m8, "DXY Index", "DXY")

# 4. TABS: OPERATIVA, CONOCIMIENTO, MAPA
st.markdown("---")
tab1, tab2, tab3 = st.tabs(["🚀 OPERATIVA SNIPER", "📚 CÓDICE DEL TRADER", "📰 NOTICIAS IA"])

with tab1:
    # Lógica del Gráfico y Análisis
    current_ticker = ticker_map.get(active_selection, "BTC-USD")
    df, date_col = get_chart_data(current_ticker)
    
    if not df.empty:
        last_price = df['Close'].iloc[-1]
        
        # Zonas Francotirador (Estilo Sentinel)
        st.subheader(f"🎯 Plan de Batalla: {active_selection}")
        z1, z2, z3 = st.columns(3)
        tp = last_price * 1.0025
        sl = last_price * 0.9975
        
        z1.metric("ENTRADA", estilo_preciso(active_selection, last_price))
        z2.metric("TAKE PROFIT", estilo_preciso(active_selection, tp))
        z3.metric("STOP LOSS", estilo_preciso(active_selection, sl))
        
        # Gráfico
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.7, 0.3], vertical_spacing=0.05)
        fig.add_trace(go.Candlestick(x=df[date_col], open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name="Precio"), row=1, col=1)
        fig.add_trace(go.Scatter(x=df[date_col], y=df['Upper'], line=dict(color='rgba(0, 255, 255, 0.2)'), name="BB Sup"), row=1, col=1)
        fig.add_trace(go.Scatter(x=df[date_col], y=df['Lower'], line=dict(color='rgba(0, 255, 255, 0.2)'), fill='tonexty', name="BB Inf"), row=1, col=1)
        fig.add_trace(go.Scatter(x=df[date_col], y=df['RSI'], line=dict(color='#ab47bc'), name="RSI"), row=2, col=1)
        fig.add_hline(y=70, line_dash="dot", row=2, col=1)
        fig.add_hline(y=30, line_dash="dot", row=2, col=1)
        fig.update_layout(template="plotly_dark", height=600, xaxis_rangeslider_visible=False, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig, use_container_width=True)
        
        # CHATBOT GEMINI
        st.divider()
        st.subheader("🤖 Mentor IA (Gemini Live)")
        if "chat_history" not in st.session_state: st.session_state.chat_history = []
        for msg in st.session_state.chat_history:
            with st.chat_message(msg["role"]): st.markdown(msg["content"])
        
        if prompt := st.chat_input(f"Consulta al Mentor sobre {active_selection}..."):
            st.session_state.chat_history.append({"role": "user", "content": prompt})
            with st.chat_message("user"): st.markdown(prompt)
            if ai_active:
                try:
                    res = model.generate_content(f"Trader experto. Activo: {active_selection}. Precio: {last_price}. RSI: {df['RSI'].iloc[-1]:.2f}. Usuario Zen: {zen_score}%. {prompt}")
                    with st.chat_message("assistant"): st.markdown(res.text)
                    st.session_state.chat_history.append({"role": "assistant", "content": res.text})
                except: st.error("Error IA")
            else: st.error("Falta API Key")

with tab2:
    st.header("📜 Leyes Inquebrantables")
    c_law1, c_law2 = st.columns(2)
    
    with c_law1:
        st.markdown("""
        <div class="wiki-card">
            <h3>1. Preservar el Capital</h3>
            <p>Si pierdes tus fichas, te echan del casino. Tu primer trabajo no es ganar dinero, es no perderlo.</p>
        </div>
        <br>
        <div class="wiki-card">
            <h3>2. Corta las pérdidas rápido</h3>
            <p>El error novato es aguantar rojos esperando un milagro. Acepta el error y sal.</p>
        </div>
        """, unsafe_allow_html=True)
        
    with c_law2:
        st.markdown("""
        <div class="wiki-card">
            <h3>3. La Tendencia es tu amiga</h3>
            <p>No intentes adivinar el techo. Fluye con el río hasta que se doble.</p>
        </div>
        <br>
        <div class="wiki-card">
            <h3>🕯️ Patrones de Poder</h3>
            <p><b>Martillo:</b> Rechazo fuerte abajo. Posible compra.</p>
            <p><b>Envolvente:</b> Una vela se come a la anterior. Cambio de mando.</p>
        </div>
        """, unsafe_allow_html=True)

with tab3:
    st.subheader("📰 Noticias con Sentimiento IA")
    try:
        news = fetch_news()
        for item in news:
            st.markdown(f"""
            <div class="news-card" style="border-left: 5px solid {item['color']} !important;">
                <div class="news-source">{item['source']}</div>
                <a href="{item['link']}" target="_blank" class="news-title">{item['title']}</a>
            </div>
            """, unsafe_allow_html=True)
    except:
        st.write("No se pudieron cargar las noticias RSS.")
