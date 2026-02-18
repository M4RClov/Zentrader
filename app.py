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
# ⚙️ CONFIGURACIÓN DEL SISTEMA
# ==========================================
st.set_page_config(page_title="ZenTrader Ultimate", layout="wide", page_icon="🧘")

# --- 🔑 TU LLAVE MAESTRA ---
API_KEY = "AIzaSyDDARUGlDLNqKy_brhfc-zWv4u1rM9mKls"  

# Configurar IA
ai_active = False
if API_KEY != "AIzaSyDDARUGlDLNqKy_brhfc-zWv4u1rM9mKls":
    try:
        genai.configure(api_key=API_KEY)
        model = genai.GenerativeModel('gemini-1.5-flash')
        ai_active = True
    except: pass

# Inicializar Analizador de Sentimiento
analyzer = SentimentIntensityAnalyzer()

# ==========================================
# 🎨 ESTÉTICA "CYBER-COLOR" (CSS AVANZADO)
# ==========================================
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;800&display=swap');
    
    /* FONDO GENERAL */
    .main { background-color: #0e1117; color: #e0e0e0; font-family: 'Poppins', sans-serif; }
    
    /* LOGO PERSONALIZADO */
    .zen-logo { font-size: 3.5rem; font-weight: 800; text-align: center; margin-bottom: 0px; letter-spacing: -1px; }
    .zen-span { color: #00e676; text-shadow: 0 0 15px rgba(0, 230, 118, 0.4); } /* Verde Neón */
    .trader-span { color: #ffab00; text-shadow: 0 0 15px rgba(255, 171, 0, 0.4); } /* Dorado */
    
    /* TARJETAS DE CRISTAL (Glassmorphism) */
    div[data-testid="stMetric"], .glass-card {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 15px;
        backdrop-filter: blur(10px);
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        transition: transform 0.2s;
    }
    div[data-testid="stMetric"]:hover { transform: translateY(-2px); border-color: #00e676; }
    
    /* COLORES DE MÉTRICAS */
    div[data-testid="stMetricLabel"] { color: #90a4ae; font-size: 0.85rem; letter-spacing: 1px; }
    div[data-testid="stMetricValue"] { font-size: 1.5rem !important; color: #ffffff; font-weight: 600; }
    
    /* RELOJES */
    .clock-box { text-align: center; padding: 10px; border-radius: 10px; background: rgba(0,0,0,0.3); border: 1px solid #333; }
    .clock-time { font-family: 'Courier New', monospace; font-size: 2.2rem; font-weight: 700; color: #00e676; }
    .clock-label { font-size: 0.8rem; color: #b0bec5; text-transform: uppercase; letter-spacing: 2px; }
    
    /* NOTICIAS */
    .news-card {
        background: #161b22; border-radius: 10px; padding: 15px; margin-bottom: 10px;
        border-left: 5px solid #555; transition: 0.3s;
    }
    .news-tag { padding: 3px 8px; border-radius: 5px; font-size: 0.7rem; font-weight: bold; color: white; margin-right: 10px; }
    .sentiment-pos { background-color: #00c853; }
    .sentiment-neg { background-color: #d50000; }
    .sentiment-neu { background-color: #607d8b; }
    
    /* AJUSTES MÓVILES */
    @media (max-width: 640px) {
        .zen-logo { font-size: 2rem; }
        .clock-time { font-size: 1.5rem; }
        .stPlotlyChart { height: 350px !important; }
    }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 🧠 CEREBRO Y DATOS
# ==========================================

def estilo_preciso(simbolo, precio):
    if precio is None or pd.isna(precio): return "0.00"
    s = str(simbolo).upper()
    if any(x in s for x in ["EURUSD", "GBPUSD", "EUR", "GBP"]): return f"{precio:.5f}"
    if "JPY" in s: return f"{precio:.3f}"
    if any(x in s for x in ["BTC", "ETH", "SOL", "XAU"]): return f"{precio:,.2f}"
    return f"{precio:,.2f}"

@st.cache_data(ttl=60)
def obtener_12_activos():
    """Descarga los 12 activos sagrados"""
    # MAPA COMPLETO DE LOS 12 ACTIVOS
    portfolio = {
        # DIVISAS & METALES
        "EUR/USD": "EURUSD=X", "DXY Index": "DX-Y.NYB", 
        "Oro (XAU)": "GC=F", "USD/JPY": "JPY=X",
        # BOLSA & ACCIONES
        "Nvidia": "NVDA", "Nasdaq": "^IXIC", 
        "S&P 500": "^GSPC", "VIX (Miedo)": "^VIX",
        # CRIPTO
        "Bitcoin": "BTC-USD", "Ethereum": "ETH-USD", 
        "Solana": "SOL-USD", "XRP": "XRP-USD"
    }
    
    resultados = {}
    for nombre, ticker in portfolio.items():
        try:
            df = yf.download(ticker, period="2d", progress=False)
            if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.droplevel(1)
            
            if not df.empty and len(df) > 0:
                precio = df['Close'].iloc[-1]
                # Calcular cambio
                if len(df) > 1:
                    previo = df['Close'].iloc[-2]
                else:
                    previo = df['Open'].iloc[-1]
                
                cambio = ((precio - previo) / previo) * 100
                resultados[nombre] = (precio, cambio)
            else:
                resultados[nombre] = (None, 0.0)
        except:
            resultados[nombre] = (None, 0.0)
            
    return resultados, portfolio

def get_chart_data(ticker):
    try:
        df = yf.download(ticker, period="1mo", interval="1h", progress=False)
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.droplevel(1)
        df = df.reset_index()
        date_col = df.columns[0]
        
        # Indicadores
        df['MA20'] = df['Close'].rolling(20).mean()
        std = df['Close'].rolling(20).std()
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

def analizar_noticia(texto):
    score = analyzer.polarity_scores(texto)['compound']
    if score >= 0.05: return "Positivo", "sentiment-pos", "#00c853"
    if score <= -0.05: return "Negativo", "sentiment-neg", "#d50000"
    return "Neutral", "sentiment-neu", "#607d8b"

def categorizar(texto):
    t = texto.lower()
    if any(x in t for x in ["bitcoin", "crypto", "btc", "eth"]): return "CRIPTO"
    if any(x in t for x in ["dolar", "fed", "tasas", "eur", "usd"]): return "FOREX/MACRO"
    if any(x in t for x in ["acciones", "nvidia", "nasdaq", "sp500"]): return "ACCIONES"
    return "MERCADO"

def fetch_colored_news():
    url = "https://es.investing.com/rss/news.rss"
    try:
        feed = feedparser.parse(url)
        items = []
        for entry in feed.entries[:8]:
            title = BeautifulSoup(entry.title, "html.parser").get_text()
            sent_label, sent_class, color_hex = analizar_noticia(title)
            cat = categorizar(title)
            items.append({
                "title": title, "link": entry.link, 
                "sent_label": sent_label, "sent_class": sent_class, 
                "cat": cat, "color": color_hex
            })
        return items
    except: return []

# ==========================================
# 🖥️ INTERFAZ DE USUARIO (UI)
# ==========================================

# 1. HEADER & RELOJES
st.markdown('<div class="zen-logo"><span class="zen-span">ZEN</span><span class="trader-span">TRADER</span></div>', unsafe_allow_html=True)

c1, c2, c3 = st.columns(3)
tzs = {"NY": "America/New_York", "LDN": "Europe/London", "TOK": "Asia/Tokyo"}

def show_clock(col, city, tz):
    time = datetime.now(pytz.timezone(tz)).strftime('%H:%M')
    col.markdown(f"""
    <div class="clock-box">
        <div class="clock-label">{city}</div>
        <div class="clock-time">{time}</div>
    </div>
    """, unsafe_allow_html=True)

show_clock(c1, "🇺🇸 NUEVA YORK", tzs["NY"])
show_clock(c2, "🇬🇧 LONDRES", tzs["LDN"])
show_clock(c3, "🇯🇵 TOKIO", tzs["TOK"])

st.markdown("---")

# 2. SIDEBAR
with st.sidebar:
    st.header("🧠 Biofeedback")
    zen_score = st.slider("Estado Mental (1-100)", 0, 100, 80)
    
    if zen_score >= 80: st.success(f"ZEN SCORE: {zen_score}% (MAESTRO)")
    elif zen_score >= 50: st.warning(f"ZEN SCORE: {zen_score}% (ATENTO)")
    else: st.error(f"ZEN SCORE: {zen_score}% (PELIGRO)")
    
    st.divider()
    # Selector sincronizado con los 12 activos
    datos_live, portfolio_map = obtener_12_activos()
    lista_nombres = list(portfolio_map.keys())
    active_selection = st.selectbox("ACTIVO A OPERAR", lista_nombres)

# 3. RADAR DE MERCADO (LOS 12 ACTIVOS)
st.subheader("📡 Radar de Inteligencia (12 Activos)")

def display_row(keys):
    cols = st.columns(4)
    for idx, key in enumerate(keys):
        val, chg = datos_live.get(key, (None, 0.0))
        with cols[idx]:
            if val:
                st.metric(key, estilo_preciso(key, val), f"{chg:.2f}%")
            else:
                st.metric(key, "Cargando...", None)

st.caption("💱 DIVISAS & MATERIAS PRIMAS")
display_row(["EUR/USD", "DXY Index", "Oro (XAU)", "USD/JPY"])

st.caption("📈 BOLSA & ÍNDICES")
display_row(["Nvidia", "Nasdaq", "S&P 500", "VIX (Miedo)"])

st.caption("🚀 CRIPTOACTIVOS")
display_row(["Bitcoin", "Ethereum", "Solana", "XRP"])

# 4. TABS: SNIPER, MAPA DE CALOR, NOTICIAS, CÓDICE
st.markdown("---")
tab1, tab2, tab3, tab4 = st.tabs(["🎯 OPERATIVA SNIPER", "🔥 MAPA DE CALOR", "📰 NOTICIAS IA", "📜 CÓDICE DEL TRADER"])

# --- TAB 1: GRÁFICO + IA ---
with tab1:
    current_ticker = portfolio_map.get(active_selection, "BTC-USD")
    df, date_col = get_chart_data(current_ticker)
    
    if not df.empty:
        last = df['Close'].iloc[-1]
        
        # Zonas
        z1, z2, z3 = st.columns(3)
        tp = last * 1.003
        sl = last * 0.997
        z1.metric("ENTRADA", estilo_preciso(current_ticker, last))
        z2.metric("TAKE PROFIT", estilo_preciso(current_ticker, tp))
        z3.metric("STOP LOSS", estilo_preciso(current_ticker, sl))
        
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
        
        # Chatbot
        st.divider()
        st.subheader("🤖 Mentor IA (Gemini)")
        if "history" not in st.session_state: st.session_state.history = []
        for m in st.session_state.history:
            with st.chat_message(m["role"]): st.markdown(m["content"])
            
        if prompt := st.chat_input(f"Pregunta sobre {active_selection}..."):
            st.session_state.history.append({"role": "user", "content": prompt})
            with st.chat_message("user"): st.markdown(prompt)
            if ai_active:
                try:
                    ctx = f"Activo: {active_selection}. Precio: {last}. RSI: {df['RSI'].iloc[-1]:.2f}. Zen: {zen_score}%. {prompt}"
                    res = model.generate_content(ctx).text
                    with st.chat_message("assistant"): st.markdown(res)
                    st.session_state.history.append({"role": "assistant", "content": res})
                except: st.error("Error IA")
            else: st.error("Falta API Key")
    else:
        st.warning("Cargando datos...")

# --- TAB 2: MAPA DE CALOR ---
with tab2:
    st.subheader("🔥 Matriz de Correlación")
    try:
        tickers_clean = list(portfolio_map.values())
        df_corr = yf.download(tickers_clean, period="1mo", progress=False)['Close'].corr()
        # Cambiamos nombres técnicos por nombres amigables en el mapa
        df_corr.index = [k for k,v in portfolio_map.items() if v in df_corr.index]
        df_corr.columns = df_corr.index
        st.dataframe(df_corr.style.background_gradient(cmap='RdYlGn', axis=None), use_container_width=True)
        st.info("💡 VERDE = Se mueven juntos (Aliados). ROJO = Se mueven opuestos (Enemigos).")
    except:
        st.write("Datos insuficientes para generar el mapa.")

# --- TAB 3: NOTICIAS DE COLORES ---
with tab3:
    st.subheader("📰 Noticias Clasificadas")
    news = fetch_colored_news()
    if news:
        c_left, c_right = st.columns(2)
        for i, item in enumerate(news):
            target = c_left if i % 2 == 0 else c_right
            with target:
                st.markdown(f"""
                <div class="news-card" style="border-left: 5px solid {item['color']} !important;">
                    <div style="margin-bottom: 5px;">
                        <span class="news-tag {item['sent_class']}">{item['sent_label']}</span>
                        <span class="news-tag" style="background:#444;">{item['cat']}</span>
                    </div>
                    <a href="{item['link']}" target="_blank" style="color:white; text-decoration:none; font-weight:600;">{item['title']}</a>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.info("No hay noticias RSS disponibles en este momento.")

# --- TAB 4: CÓDICE (REGLAS DE COLORES) ---
with tab4:
    st.header("📜 Leyes Inquebrantables")
    
    col_a, col_b = st.columns(2)
    
    with col_a:
        st.error("1. PRESERVAR EL CAPITAL")
        st.caption("Si pierdes tus fichas, te echan del casino. Tu primer trabajo es no perder.")
        
        st.warning("2. CORTA LAS PÉRDIDAS RÁPIDO")
        st.caption("No reces. Si toca el Stop Loss, acepta y sal. Mañana es otro día.")
        
        st.success("3. LA TENDENCIA ES TU AMIGA")
        st.caption("No intentes adivinar el techo. Nada en el río, no contra él.")

    with col_b:
        st.info("🕯️ EL MARTILLO (HAMMER)")
        st.caption("Rechazo fuerte abajo. Los compradores han despertado.")
        
        st.error("🕯️ LA ENVOLVENTE (ENGULFING)")
        st.caption("Una vela se come a la anterior. Cambio brutal de control.")
        
        st.warning("🕯️ DOJI (INDECISIÓN)")
        st.caption("Nadie gana. Prepárate para un movimiento violento.")

