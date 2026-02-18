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

# Configurar IA (Manejo de errores si no hay clave)
ai_active = False
if API_KEY != "AIzaSyDDARUGlDLNqKy_brhfc-zWv4u1rM9mKls":
    try:
        genai.configure(api_key=API_KEY)
        model = genai.GenerativeModel('gemini-1.5-flash')
        ai_active = True
    except:
        pass

# Inicializar VADER para noticias
analyzer = SentimentIntensityAnalyzer()

# ==========================================
# 🎨 ESTÉTICA "CYBER-ZEN" (CSS PRO)
# ==========================================
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600&display=swap');
    
    /* FONDO Y TEXTO */
    .main { background-color: #0e1117; color: #e0e0e0; font-family: 'Poppins', sans-serif; }
    
    /* TARJETAS DE CRISTAL (Glassmorphism) */
    div[data-testid="stMetric"], .glass-card, .news-card {
        background-color: rgba(255, 255, 255, 0.03) !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        border-radius: 12px;
        padding: 15px;
        backdrop-filter: blur(10px);
        box-shadow: 0 4px 6px rgba(0,0,0,0.2);
    }
    
    /* TÍTULOS */
    h1, h2, h3 { color: #ffffff; font-weight: 600; letter-spacing: 1px; }
    .zen-title { font-size: 2.5rem; background: -webkit-linear-gradient(#26a69a, #4db6ac); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
    
    /* METRICAS */
    div[data-testid="stMetricValue"] { font-size: 1.4rem !important; color: #ffffff; }
    div[data-testid="stMetricLabel"] { color: #90a4ae; font-size: 0.9rem; }
    
    /* RELOJES */
    .clock-time { font-family: 'Courier New', monospace; font-size: 1.8em; font-weight: bold; color: #4db6ac; }
    .clock-city { font-size: 0.8em; color: #78909c; text-transform: uppercase; letter-spacing: 2px; }
    
    /* AJUSTE MOVIL */
    @media (max-width: 640px) {
        .stPlotlyChart { height: 400px !important; }
    }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 🧠 FUNCIONES DEL NÚCLEO
# ==========================================

def estilo_preciso(simbolo, precio):
    """Formato inteligente de 5 decimales"""
    if precio is None or pd.isna(precio): return "0.00"
    s = str(simbolo).upper()
    if any(x in s for x in ["EURUSD", "GBPUSD", "EUR", "GBP"]): return f"{precio:.5f}"
    if "JPY" in s: return f"{precio:.3f}"
    if any(x in s for x in ["BTC", "ETH", "XAU"]): return f"{precio:,.2f}"
    return f"{precio:,.2f}"

@st.cache_data(ttl=60)
def obtener_precios_live():
    """Descarga robusta para evitar 'nan'"""
    tickers = {
        "Bitcoin": "BTC-USD", "Ethereum": "ETH-USD", 
        "S&P 500": "^GSPC", "Nvidia": "NVDA", "Oro": "GC=F",
        "EUR/USD": "EURUSD=X", "GBP/USD": "GBPUSD=X", "DXY": "DX-Y.NYB"
    }
    data = {}
    # Descargamos uno por uno para asegurar que si uno falla, el resto cargue
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
    """Datos para el gráfico con FECHAS REALES"""
    try:
        df = yf.download(ticker, period="1mo", interval="1h", progress=False)
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.droplevel(1)
        df = df.reset_index()
        
        # Detectar columna fecha
        date_col = df.columns[0]
        
        # Indicadores
        df['MA20'] = df['Close'].rolling(window=20).mean()
        std = df['Close'].rolling(window=20).std()
        df['Upper'] = df['MA20'] + (std * 2)
        df['Lower'] = df['MA20'] - (std * 2)
        
        # RSI
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
    """Noticias con sentimiento"""
    url = "https://es.investing.com/rss/news.rss"
    feeds = feedparser.parse(url)
    news_items = []
    for entry in feeds.entries[:4]:
        title = clean_html(entry.title)
        sentiment = analyzer.polarity_scores(title)['compound']
        color = "#00e676" if sentiment > 0.05 else "#ff1744" if sentiment < -0.05 else "#b0bec5"
        news_items.append({"title": title, "link": entry.link, "color": color})
    return news_items

# ==========================================
# 🖥️ UI PRINCIPAL
# ==========================================

# --- 1. ENCABEZADO Y RELOJES ---
col_logo, col_relojes = st.columns([1, 2])
with col_logo:
    st.markdown('<div class="zen-title">ZENTRADER</div>', unsafe_allow_html=True)
    st.caption("SENTINEL v2.0 | IA ACTIVA")

with col_relojes:
    c1, c2, c3 = st.columns(3)
    tzs = {"NY": "America/New_York", "LDN": "Europe/London", "TOK": "Asia/Tokyo"}
    
    def show_clock(col, city, tz):
        time = datetime.now(pytz.timezone(tz)).strftime('%H:%M')
        col.markdown(f"""
        <div style="text-align: center;">
            <div class="clock-time">{time}</div>
            <div class="clock-city">{city}</div>
        </div>
        """, unsafe_allow_html=True)

    show_clock(c1, "NEW YORK", tzs["NY"])
    show_clock(c2, "LONDON", tzs["LDN"])
    show_clock(c3, "TOKYO", tzs["TOK"])

st.markdown("---")

# --- 2. SIDEBAR (BIOFEEDBACK) ---
with st.sidebar:
    st.header("🛡️ Biofeedback")
    zen_score = st.slider("Nivel de Calma (1-10)", 1, 10, 7)
    score_pct = zen_score * 10
    
    if score_pct < 50:
        st.error(f"ZEN SCORE: {score_pct}% (RIESGO)")
    else:
        st.success(f"ZEN SCORE: {score_pct}% (ÓPTIMO)")
    
    st.divider()
    active_selection = st.selectbox("ACTIVO PRINCIPAL", ["Bitcoin", "EUR/USD", "Oro", "S&P 500", "Nvidia"])

# --- 3. CINTA DE PRECIOS (LIVE) ---
market_data, ticker_map = obtener_precios_live()
st.subheader("📡 Radar de Mercado")

# Fila 1
m1, m2, m3, m4 = st.columns(4)
def card(col, label, key):
    val, chg = market_data.get(key, (None, 0.0))
    if val: 
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

# --- 4. ZONA OPERATIVA (GRÁFICO + IA) ---
st.markdown("---")
tab1, tab2, tab3 = st.tabs(["🚀 GRÁFICO & IA", "🔥 MAPA DE CALOR", "📰 NOTICIAS"])

with tab1:
    current_ticker = ticker_map.get(active_selection, "BTC-USD")
    df, date_col = get_chart_data(current_ticker)
    
    if not df.empty:
        last_price = df['Close'].iloc[-1]
        rsi_val = df['RSI'].iloc[-1]
        
        # ZONAS SNIPER
        st.subheader(f"🎯 Francotirador: {active_selection}")
        z1, z2, z3 = st.columns(3)
        tp = last_price * 1.0025
        sl = last_price * 0.9975
        
        z1.metric("ENTRADA", estilo_preciso(active_selection, last_price))
        z2.metric("TAKE PROFIT", estilo_preciso(active_selection, tp))
        z3.metric("STOP LOSS", estilo_preciso(active_selection, sl))
        
        # GRÁFICO PLOTLY
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.7, 0.3], vertical_spacing=0.05)
        
        # Velas
        fig.add_trace(go.Candlestick(x=df[date_col], open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name="Precio"), row=1, col=1)
        # Bollinger
        fig.add_trace(go.Scatter(x=df[date_col], y=df['Upper'], line=dict(color='rgba(0, 255, 255, 0.2)'), name="BB Sup"), row=1, col=1)
        fig.add_trace(go.Scatter(x=df[date_col], y=df['Lower'], line=dict(color='rgba(0, 255, 255, 0.2)'), fill='tonexty', name="BB Inf"), row=1, col=1)
        # RSI
        fig.add_trace(go.Scatter(x=df[date_col], y=df['RSI'], line=dict(color='#ab47bc'), name="RSI"), row=2, col=1)
        fig.add_hline(y=70, line_dash="dot", row=2, col=1)
        fig.add_hline(y=30, line_dash="dot", row=2, col=1)
        
        fig.update_layout(template="plotly_dark", height=600, xaxis_rangeslider_visible=False, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig, use_container_width=True)
        
        # CHATBOT GEMINI INTEGRADO
        st.divider()
        st.subheader("🤖 Mentor IA (Análisis Táctico)")
        
        if "chat_history" not in st.session_state:
            st.session_state.chat_history = []

        for msg in st.session_state.chat_history:
            with st.chat_message(msg["role"]): st.markdown(msg["content"])

        if prompt := st.chat_input(f"Consulta sobre {active_selection}..."):
            st.session_state.chat_history.append({"role": "user", "content": prompt})
            with st.chat_message("user"): st.markdown(prompt)
            
            with st.chat_message("assistant"):
                if ai_active:
                    try:
                        context = f"""
                        Eres un trader experto. Activo: {active_selection}.
                        Precio: {estilo_preciso(active_selection, last_price)}.
                        RSI: {rsi_val:.2f}. Zen Score: {score_pct}%.
                        Responde breve y profesionalmente.
                        """
                        res = model.generate_content(context + " " + prompt)
                        st.markdown(res.text)
                        st.session_state.chat_history.append({"role": "assistant", "content": res.text})
                    except Exception as e:
                        st.error(f"Error IA: {e}")
                else:
                    st.warning("⚠️ Configura tu API KEY en el código.")
    else:
        st.warning("Cargando datos... (Si persiste, revisa tu conexión)")

with tab2:
    st.subheader("🔥 Mapa de Sinergia")
    # Simulación de heatmap (Correlation Matrix)
    st.info("Correlaciones de Mercado (Últimos 30 días)")
    tickers_list = list(ticker_map.values())[:5]
    try:
        df_corr = yf.download(tickers_list, period="1mo", progress=False)['Close'].corr()
        st.dataframe(df_corr.style.background_gradient(cmap='RdYlGn'), use_container_width=True)
    except:
        st.write("Datos insuficientes para matriz.")

with tab3:
    st.subheader("📰 Noticias de Impacto")
    try:
        news = fetch_news()
        for item in news:
            st.markdown(f"""
            <div class="news-card" style="border-left: 5px solid {item['color']} !important;">
                <a href="{item['link']}" target="_blank" style="text-decoration: none; color: white;">
                    <b>{item['title']}</b>
                </a>
            </div>
            """, unsafe_allow_html=True)
    except:
        st.write("No se pudieron cargar las noticias RSS.")
        st.write("No se pudieron cargar las noticias RSS.")

