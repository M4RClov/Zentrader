import streamlit as st
import pandas as pd
import yfinance as yf
import feedparser
import time
import os
from datetime import datetime
import pytz
from bs4 import BeautifulSoup
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

import io
from gtts import gTTS

# Inicializar el analizador de sentimientos una sola vez
analyzer = SentimentIntensityAnalyzer()

# Configuración de la página
st.set_page_config(
    page_title="ZenTrader Sentinel",
    page_icon="🧘",
    layout="wide"
)

# Estilos CSS personalizados para "Clean UI"
st.markdown("""
    <style>
    .main {
        background-color: #0e1117;
        color: #fafafa;
    }
    .stButton>button {
        width: 100%;
        border-radius: 20px;
    }
    .big-font {
        font-size: 20px !important;
        font-weight: 300;
    }
    .warning-box {
        padding: 20px;
        background-color: #3b1e1e;
        border-left: 5px solid #ff4b4b;
        border-radius: 5px;
        margin-top: 20px;
    }
    .success-box {
        padding: 20px;
        background-color: #1e3b2e;
        border-left: 5px solid #27ae60;
        border-radius: 5px;
        margin-top: 20px;
    }
    .news-card {
        padding: 15px;
        background-color: #1e2530;
        border-radius: 10px;
        margin-bottom: 10px;
        border-left: 4px solid #4caf50;
    }
    .news-source {
        font-size: 0.8em;
        color: #888;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    .sentiment-badge {
        font-size: 0.8em;
        padding: 2px 8px;
        border-radius: 12px;
        font-weight: bold;
        margin-left: 10px;
        color: white;
    }
    .category-badge {
        font-size: 0.7em;
        padding: 4px 8px;
        border-radius: 4px;
        font-weight: bold;
        margin-right: 10px;
        color: white;
        text-transform: uppercase;
        display: inline-block;
    }
    /* --- CYBER-ZEN PREMIUM UI (Phase 29) --- */
    h3 {
        border-left: 5px solid #26a69a; /* Barra Turquesa */
        padding-left: 15px;
        margin-top: 30px;
        color: #e0e0e0;
    }
    
    /* Contenedores tipo "Tarjeta" */
    .stExpander, div[data-testid="stContainer"] {
        background-color: rgba(255, 255, 255, 0.03); /* Fondo sutil */
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 10px;
        padding: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
        margin-bottom: 20px; /* Separación automática */
    }

    /* Eliminar líneas raras de Streamlit */
    hr {
        border-color: rgba(255, 255, 255, 0.1);
        margin-top: 1rem;
        margin-bottom: 1rem;
    }
    </style>
    """, unsafe_allow_html=True)

def clean_html(text):
    if not text:
        return ""
    soup = BeautifulSoup(text, "html.parser")
    return soup.get_text()

def categorize_news(title, summary, source):
    text = (title + " " + summary).lower()
    source = source.lower()
    
    # 1. GEOPOLÍTICA (Alta Prioridad - Phase 11)
    if any(x in text for x in ["guerra", "conflicto", "arancel", "china", "rusia", "eeuu", "biden", "trump", "sanciones", "pib", "inflación", "inflation", "war"]):
        return "GEOPOLÍTICA", "#C70039" # Rojo Intenso
        
    # 2. CRIPTO
    if "cointelegraph" in source or any(x in text for x in ["bitcoin", "btc", "ethereum", "eth", "cripto", "crypto", "blockchain", "solana", "xrp"]):
        return "CRIPTO", "#F7931A"
    # 3. METALES
    if any(x in text for x in ["oro", "gold", "xau", "plata", "silver", "metal"]):
        return "METALES", "#FFD700"
    # 4. MATERIAS PRIMAS / PETROLEO
    if any(x in text for x in ["petróleo", "petroleo", "oil", "crudo", "litio", "lithium", "cobre", "copper", "energy", "energía"]):
        return "MATERIAS PRIMAS", "#8A2BE2"
    # 5. FIAT / FOREX / BANCOS
    if any(x in text for x in ["dólar", "dolar", "usd", "euro", "eur", "yen", "jpy", "fed", "bancos", "central bank", "tasas", "rates", "forex"]):
        return "FIAT / FOREX", "#4169E1"
    # 6. Default
    return "MERCADOS", "#008080" # Teal

def get_sentiment(text):
    if not text:
        return 0, "Neutral", "#7f8c8d" # Gris
    
    scores = analyzer.polarity_scores(text)
    compound = scores['compound']
    
    if compound >= 0.05:
        return compound, "Positivo", "#27ae60" # Verde
    elif compound <= -0.05:
        return compound, "Negativo", "#c0392b" # Rojo
    else:
        return compound, "Neutral", "#7f8c8d" # Gris

def calculate_zen_score(mood, sleep, stress, meal, nature):
    """
    Calcula el Zen Score (0-100) y devuelve el score y una lista de razones/consejos.
    """
    # Base Score: Mood * 5 + 50 (Range 55-100 for decent mood)
    # Ejemplo: Mood 1 -> 55. Mood 5 -> 75. Mood 10 -> 100.
    score = 50 + (mood * 5)
    reasons = []

    # Penalizaciones
    if sleep < 6:
        score -= 30
        reasons.append("⚠️ **Sueño Insuficiente:** Reduce función cognitiva y control de impulsos.")
    
    if stress > 7:
        score -= 40
        reasons.append("⚠️ **Alerta de Cortisol:** Visión de túnel inminente. Riesgo alto de 'Revenge Trading'.")
    
    if meal == "Azúcar/Procesados":
        score -= 20
        reasons.append("⚠️ **Pico Glucémico:** Probable niebla mental en breve.")
    
    # Bonificaciones
    if nature:
        score += 20
        reasons.append("🌿 **Factor Naturaleza:** Claridad mental aumentada.")

    # Clamp score 0-100
    score = max(0, min(100, score))
    
    return score, reasons

@st.cache_data(ttl=3600) # Cache de 1 hora
def obtener_calendario_economico():
    try:
        url = "https://es.investing.com/rss/calendar.rss"
        feed = feedparser.parse(url)
        return feed.entries[:5] # Retornamos los 5 primeros
    except:
        return []

def get_market_prices():
    tickers = {
        # Cripto
        "BTC-USD": "Bitcoin",
        "ETH-USD": "Ethereum",
        "SOL-USD": "Solana",
        "XRP-USD": "XRP",
        
        # Metales / Forex / Macro
        "GC=F": "Oro",
        "EURUSD=X": "EUR/USD",
        "DX-Y.NYB": "Índice Dólar",
        "JPY=X": "USD/JPY",
        
        # Tradicional
        "^GSPC": "S&P 500",
        "^IXIC": "Nasdaq",
        "NVDA": "Nvidia",
        "^VIX": "VIX (Miedo)"
    }
    
    data = {}
    
    try:
        ticker_strings = " ".join(list(tickers.keys()))
        df = yf.download(ticker_strings, period="1d", progress=False)['Close']
        
        for symbol, name in tickers.items():
            try:
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period="2d")
                
                if len(hist) >= 2:
                    current_price = hist['Close'].iloc[-1]
                    prev_close = hist['Close'].iloc[-2]
                    change = ((current_price - prev_close) / prev_close) * 100
                    data[name] = (current_price, change)
                elif len(hist) == 1:
                    current_price = hist['Close'].iloc[-1]
                    open_price = hist['Open'].iloc[-1]
                    change = ((current_price - open_price) / open_price) * 100
                    data[name] = (current_price, change)
                else:
                    data[name] = (0.0, 0.0)
            except:
                data[name] = None 
                
    except Exception as e:
        pass
        
    return data

@st.cache_data(ttl=300) # Cache de 5 minutos
def scan_market():
    watchlist = ['BTC-USD', 'ETH-USD', 'SOL-USD', 'GC=F', 'DX-Y.NYB', 'EURUSD=X', 'JPY=X', '^GSPC', '^IXIC', 'NVDA', 'XRP-USD', '^VIX']
    results = []
    
    for ticker_symbol in watchlist:
        try:
            # Descargar 1 mes de datos DE UNO EN UNO para seguridad
            df = yf.download(ticker_symbol, period="1mo", interval="1d", progress=False)
            
            # Validación de integridad básica
            if df.empty or len(df) < 15:
                continue
                
            # Limpieza MultiIndex si existe
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.droplevel(1)
            
            # Precio Actual
            current_price = df['Close'].iloc[-1]
            
            # SMA 20
            df['SMA20'] = df['Close'].rolling(window=20).mean()
            sma_val = df['SMA20'].iloc[-1]
            
            # RSI 14
            delta = df['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            df['RSI'] = 100 - (100 / (1 + rs))
            rsi_val = df['RSI'].iloc[-1]
            
            # Bandas Bollinger
            std = df['Close'].rolling(window=20).std()
            bb_upper = df['SMA20'].iloc[-1] + (std.iloc[-1] * 2)
            bb_lower = df['SMA20'].iloc[-1] - (std.iloc[-1] * 2)
            
            # Lógica de Estado
            trend = "Alcista 🟢" if current_price > sma_val else "Bajista 🔴"
            
            status = "Normal"
            if rsi_val < 30:
                status = "SOBREVENTA (Oportunidad?)"
            elif rsi_val > 70:
                status = "SOBRECOMPRA (Cuidado)"
            elif current_price < bb_lower:
                status = "ROMPIENDO SUELO 📉"
            elif current_price > bb_upper:
                status = "ROMPIENDO TECHO 📈"
            
            results.append({
                "Activo": ticker_symbol,
                "Precio": current_price,
                "RSI (14)": rsi_val,
                "Tendencia": trend,
                "Estado": status
            })
            
        except Exception:
            continue
    
    # Retornamos un DataFrame simple
    return pd.DataFrame(results)

def get_styled_scanner():
    df = scan_market()
    if df.empty:
        return None
        
    def highlight_rsi(val):
        color = ''
        if val > 70: color = 'color: #ef5350; font-weight: bold' # Rojo
        elif val < 30: color = 'color: #66bb6a; font-weight: bold' # Verde
        return color
        
    def highlight_status(val):
        color = ''
        if "SOBRE" in val or "ROMPIENDO" in val:
             color = 'background-color: rgba(255, 255, 255, 0.1); font-weight: bold'
        return color

    return df.style.map(highlight_rsi, subset=['RSI (14)'])\
                   .map(highlight_status, subset=['Estado'])\
                   .format({"Precio": "{:.2f}", "RSI (14)": "{:.1f}"})

@st.cache_data(ttl=3600) # Cache de 1 hora
def get_correlation_matrix():
    tickers = ['BTC-USD', 'ETH-USD', 'SOL-USD', 'GC=F', 'DX-Y.NYB', 'EURUSD=X', '^GSPC', '^IXIC', 'NVDA', 'XRP-USD']
    # Mapa de nombres amigables
    friendly_names = {
        'BTC-USD': 'BTC', 'ETH-USD': 'ETH', 'SOL-USD': 'SOL', 'GC=F': 'ORO',
        'DX-Y.NYB': 'DXY', 'EURUSD=X': 'EUR', '^GSPC': 'SP500', '^IXIC': 'NAS',
        'NVDA': 'NVDA', 'XRP-USD': 'XRP'
    }
    
    try:
        # Descarga masiva para correlación (3 meses)
        data = yf.download(tickers, period="3mo", interval="1d", progress=False)['Close']
        if data.empty: return None
        
        # Limpieza (MultiIndex)
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = [c[1] if isinstance(c, tuple) else c for c in data.columns]
            
        # Renombrar columnas
        data.rename(columns=friendly_names, inplace=True)
        
        # Calcular Matriz
        corr_matrix = data.corr()
        return corr_matrix
        
    except Exception:
        return None

def style_correlation(df):
    return df.style.background_gradient(cmap='RdYlGn', vmin=-1.0, vmax=1.0).format("{:.2f}")

def display_mentor_analysis(analysis_data, asset_name, account_capital=1000, risk_pct=1.0):
    if not analysis_data:
        return

    price = analysis_data['price']
    sma = analysis_data['sma']
    rsi = analysis_data['rsi']
    macd = analysis_data['macd']
    macd_signal = analysis_data['macd_signal']
    atr = analysis_data['atr']
    
    st.markdown(f"### 🔮 El Oráculo (Mentoría IA): {asset_name}")
    
    with st.container():
        # --- LÓGICA DEL ORÁCULO (VEREDICTO) ---
        verdict_title = "ANÁLISIS NEUTRAL"
        verdict_msg = "El mercado está indeciso. Espera una mejor configuración."
        verdict_type = "info" # success, warning, error, info
        
        # 1. DISPARO ALCISTA
        if price > sma and macd > macd_signal and rsi < 70:
            verdict_title = "🚀 DISPARO ALCISTA DETECTADO"
            verdict_msg = "CONFIRMACIÓN DE FUERZA: Los indicadores se alinean al alza. El precio está sobre la media, el momentum (MACD) es positivo y hay espacio en el RSI."
            verdict_type = "success"
            
        # 2. DISPARO BAJISTA
        elif price < sma and macd < macd_signal and rsi > 30:
            verdict_title = "📉 DISPARO BAJISTA DETECTADO"
            verdict_msg = "PRESIÓN DE VENTA CONFIRMADA: La estructura técnica favorece a los osos. Precio bajo la media y momentum negativo."
            verdict_type = "error" # Usamos rojo para bajista
            
        # 3. AGOTAMIENTO (Divergencia o Sobrecompra Extrema)
        elif rsi > 75 or (price > sma and macd < macd_signal):
             verdict_title = "⚠️ ALERTA DE AGOTAMIENTO / TECHO"
             verdict_msg = "El precio sube pero pierde fuerza interna (Divergencia o RSI Extremo). Peligro de reversión inminente."
             verdict_type = "warning"
             
        # 4. RUIDO / LATERAL
        elif abs(macd - macd_signal) < 0.1 and atr < (price * 0.005): # ATR muy bajo (<0.5%)
             verdict_title = "💤 MERCADO DORMIDO (RUIDO)"
             verdict_msg = "Baja volatilidad y momentum plano. No fuerces operaciones donde no las hay. El mercado está descansando."
             verdict_type = "info"

        # --- VISUALIZACIÓN DEL VEREDICTO ---
        if verdict_type == "success":
            st.success(f"**{verdict_title}**\n\n{verdict_msg}")
        elif verdict_type == "error":
            st.error(f"**{verdict_title}**\n\n{verdict_msg}")
        elif verdict_type == "warning":
            st.warning(f"**{verdict_title}**\n\n{verdict_msg}")
        else:
            st.info(f"**{verdict_title}**\n\n{verdict_msg}")

        # --- CHECKLIST DE CONFLUENCIA (Phase 28) ---
        st.markdown("#### ✅ Lista de Confirmación (Semáforo)")
        
        # Lógica de estados
        check_trend = price > sma
        check_momentum = macd > macd_signal
        check_rsi_safe = 40 < rsi < 70
        bb_upper = analysis_data['bb_upper']
        bb_lower = analysis_data['bb_lower']
        check_structure = bb_lower < price < bb_upper
        
        # Conteo de Aciertos
        checks_passed = sum([check_trend, check_momentum, check_rsi_safe, check_structure])
        
        # Columnas Visuales
        col_c1, col_c2, col_c3, col_c4 = st.columns(4)
        
        with col_c1:
            if check_trend:
                st.success("✅ TENDENCIA")
                st.caption("A favor (Sup. SMA20)")
            else:
                st.error("❌ TENDENCIA")
                st.caption("En contra (Inf. SMA20)")
                
        with col_c2:
            if check_momentum:
                st.success("✅ MOMENTUM")
                st.caption("Acelerando (MACD Bull)")
            else:
                st.warning("⚠️ MOMENTUM")
                st.caption("Frenando (MACD Bear)")
                
        with col_c3:
            if check_rsi_safe:
                st.success("✅ GASOLINA")
                st.caption("RSI Sano (40-70)")
            else:
                st.warning("⚠️ EXTREMO")
                st.caption("RSI Sobrecargado")
                
        with col_c4:
            if check_structure:
                st.success("✅ RANGO")
                st.caption("Dentro de bandas")
            else:
                st.warning("⚠️ RUPTURA")
                st.caption("Fuera de bandas")
                
        # Conclusión Visual
        if checks_passed >= 3:
            st.info("🌟 **SETUP DE ALTA CALIDAD:** La mayoría de las luces están verdes. Probabilidad a favor.")
        else:
            st.warning("✋ **CONDICIONES MIXTAS:** Hay señales contradictorias. Reduce riesgo o espera.")

        # --- ASESOR DE VOZ (Phase 32) ---
        # Recuperamos estado del sidebar (pasado via args o session_state, 
        # pero como no cambiamos la firma de todas las funciones, usaremos una key global si es necesario
        # o asumimos que se pasa. Mejor: Usar st.session_state directamente para la config de voz)
        
        if st.session_state.get('voice_active', False):
            if st.button("🔊 Escuchar Informe Táctico"):
                # Generar guion
                trend_speak = "Alcista" if check_trend else "Bajista"
                mom_speak = "Positivo" if check_momentum else "Negativo"
                verdict_speak = "Alta Calidad" if checks_passed >=3 else "Precaución"
                
                texto_voz = f"Atención operador. Análisis de {asset_name}. Tendencia {trend_speak}. Momentum {mom_speak}. Situación de {verdict_speak}. {verdict_msg}"
                
                try:
                    tts = gTTS(text=texto_voz, lang='es')
                    buffer = io.BytesIO()
                    tts.write_to_fp(buffer)
                    buffer.seek(0)
                    st.audio(buffer, format='audio/mp3')
                except Exception as e:
                    st.error(f"Error de audio: {e}")

        st.caption("🎓 *Recuerda: El Oráculo interpreta probabilidades, no predice el futuro. Tú eres el ejecutor.*")
        
        # Spacer limpio en vez de divider (Phase 29)
        st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True) 
        
        st.subheader("🎯 Zonas de Francotirador (Plan de Batalla)")
        
        col_plan1, col_plan2, col_plan3 = st.columns(3)
        
        # --- COLUMNA 1: LA OFERTA (S1 - Compra) ---
        s1 = analysis_data.get('s1', 0)
        dist_s1_pct = abs(price - s1) / price
        
        with col_plan1:
            st.metric("1. LA OFERTA (Zona Compra)", f"${s1:,.2f}")
            if price > s1:
                if dist_s1_pct < 0.005: # Menos de 0.5% de distancia
                    st.success("✅ **ESTAMOS EN ZONA.** El precio está probando la oferta. Busca patron de giro.")
                else:
                    st.info(f"⏳ **PACIENCIA.** Espera retroceso a ${s1:,.2f}. No persigas el precio.")
            else:
                st.error("⚠️ **SOPORTE ROTO.** El precio cayó bajo la zona de compra. Espera recuperación.")

        # --- COLUMNA 2: EL TECHO (R1 - Take Profit) ---
        r1 = analysis_data.get('r1', 0)
        with col_plan2:
            st.metric("2. EL TECHO (Take Profit)", f"${r1:,.2f}")
            st.caption("Objetivo lógico basado en estructura previa.")

        # --- COLUMNA 3: PROTECCIÓN (Stop Loss Dinámico) ---
        # Stop Loss = Precio - 2*ATR (Para largos) o Precio + 2*ATR (Para cortos)
        # Asumimos logica defensiva general basada en volatilidad
        sl_suggested = price - (2 * atr)
        with col_plan3:
            st.metric("3. PROTECCIÓN (Stop Loss)", f"${sl_suggested:,.2f}")
            st.caption(f"Basado en volatilidad real (2x ATR: {atr:.2f}).")
            
            # --- CÁLCULO FANTASMA DE POSICIÓN (Phase 27) ---
            if price > sma: # Solo mostramos cálculo si estamos en zona alcista
                distancia = price - sl_suggested
                if distancia > 0:
                    dinero_riesgo = account_capital * (risk_pct / 100)
                    units_sugg = dinero_riesgo / distancia
                    
                    st.markdown(f"**⚖️ Tamaño Sugerido:** `{units_sugg:.4f}` Unidades")
                    st.caption(f"Arriesgando solo ${dinero_riesgo:.2f} ({risk_pct}%)")
            else:
                st.caption("✋ Esperar confirmación de tendencia para calcular tamaño.")

        # --- BARRA DE PROBABILIDAD ---
        st.markdown("#### 🎲 Probabilidad Técnica del Setup")
        
        prob_score = 50 # Base neutral
        
        # Factores Alcistas
        if price > sma: prob_score += 20
        if macd > macd_signal: prob_score += 10
        if rsi < 40: prob_score += 10 # Espacio para subir
        
        # Factores Bajistas
        if price < sma: prob_score -= 20
        if macd < macd_signal: prob_score -= 10
        if rsi > 70: prob_score -= 10 # Sobreextendido
        
        # Limites
        prob_score = max(0, min(100, prob_score))
        
        # Color de barra
        bar_color = "red"
        if prob_score > 60: bar_color = "green"
        elif 40 <= prob_score <= 60: bar_color = "yellow"
        
        st.progress(prob_score / 100, text=f"Probabilidad Alcista Estimada: {prob_score}%")
        if prob_score > 70:
            st.caption("🔥 **Alta probabilidad de éxito en largos.**")
        elif prob_score < 30:
            st.caption("🐻 **Alta probabilidad de caída (Shorts).**")
        else:
            st.caption("⚖️ **Escenario Mixto/Rango.**")

def create_chart(ticker, name, timeframe_interval="1d", timeframe_period="1y", show_rsi=False, show_bb=False):
    analysis_data = {}
    try:
        # Descargar historial (Dinámico según temporalidad)
        data = yf.download(ticker, period=timeframe_period, interval=timeframe_interval, progress=False)
        
        if data.empty:
            st.warning(f"No hay datos suficientes para graficar {name}.")
            return None, None
        
        # CORRECCIÓN GRÁFICOS: Manejo robusto de MultiIndex y Reset Index
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.droplevel(1)
            
        data = data.reset_index()
            
        # Calcular SMA 20
        data['SMA20'] = data['Close'].rolling(window=20).mean()

        # Calcular Bollinger Bands (20, 2)
        # Siempre calculamos BB para el Mentor, aunque no se muestren
        data['BB_Upper'] = data['SMA20'] + (data['Close'].rolling(window=20).std() * 2)
        data['BB_Lower'] = data['SMA20'] - (data['Close'].rolling(window=20).std() * 2)

        # Calcular RSI (14)
        delta = data['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        data['RSI'] = 100 - (100 / (1 + rs))

        # --- CÁLCULO DE MACD (12, 26, 9) ---
        ema12 = data['Close'].ewm(span=12, adjust=False).mean()
        ema26 = data['Close'].ewm(span=26, adjust=False).mean()
        data['MACD'] = ema12 - ema26
        data['MACD_Signal'] = data['MACD'].ewm(span=9, adjust=False).mean()

        # --- CÁLCULO DE ATR (14) ---
        high_low = data['High'] - data['Low']
        high_close = (data['High'] - data['Close'].shift()).abs()
        low_close = (data['Low'] - data['Close'].shift()).abs()
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = ranges.max(axis=1)
        data['ATR'] = true_range.rolling(window=14).mean()

        # --- CÁLCULO DE PIVOTES (Classic) ---
        # Basado en la vela ANTERIOR (Confirmada)
        if len(data) >= 2:
            prev_candle = data.iloc[-2]
            pp = (prev_candle['High'] + prev_candle['Low'] + prev_candle['Close']) / 3
            r1 = (2 * pp) - prev_candle['Low']
            s1 = (2 * pp) - prev_candle['High']
        else:
            pp = r1 = s1 = data['Close'].iloc[-1] # Fallback
            
        # --- EXTRACCIÓN DE DATOS PARA MENTOR ---
        last_row = data.iloc[-1]
        analysis_data = {
            'price': last_row['Close'],
            'sma': last_row['SMA20'],
            'rsi': last_row['RSI'],
            'bb_upper': last_row['BB_Upper'],
            'bb_lower': last_row['BB_Lower'],
            'macd': last_row['MACD'],
            'macd_signal': last_row['MACD_Signal'],
            'atr': last_row['ATR'],
            's1': s1,
            'r1': r1
        }
        
        # Recortar datos para mostrar solo los últimos 3 meses visibles
        visible_data = data.tail(90).reset_index(drop=True)
        
        # Definir Filas del Subplot (Si RSI está activo usamos 2 filas, sino 1)
        if show_rsi:
            fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                                vertical_spacing=0.05, 
                                row_heights=[0.7, 0.3])
        else:
            fig = make_subplots(rows=1, cols=1)
        
        # --- FILA 1: PRECIO ---
        date_col = 'Date' if 'Date' in visible_data.columns else visible_data.columns[0]
        
        # Velas
        fig.add_trace(go.Candlestick(x=visible_data[date_col],
                        open=visible_data['Open'],
                        high=visible_data['High'],
                        low=visible_data['Low'],
                        close=visible_data['Close'],
                        name='Precio',
                        increasing_line_color='#26a69a', 
                        decreasing_line_color='#ef5350'), row=1, col=1)
                        
        # SMA 20
        fig.add_trace(go.Scatter(x=visible_data[date_col], y=visible_data['SMA20'], 
                                 mode='lines', 
                                 name='SMA 20',
                                 line=dict(color='blue', width=1.5)), row=1, col=1)

        # --- FILA 2: RSI ---
        if show_rsi:
            fig.add_trace(go.Scatter(x=visible_data[date_col], y=visible_data['RSI'], 
                                    mode='lines', name='RSI',
                                    line=dict(color='purple', width=2)), row=2, col=1)
            # Líneas de referencia RSI (70/30)
            fig.add_hline(y=70, line_dash="dot", line_color="red", row=2, col=1)
            fig.add_hline(y=30, line_dash="dot", line_color="green", row=2, col=1)
            fig.update_yaxes(title_text="RSI", row=2, col=1, range=[0,100])

        # Diseño General
        fig.update_layout(
            title=f"{name} - Acción de Precio ({timeframe_interval})",
            yaxis_title='Precio',
            xaxis_rangeslider_visible=False,
            template="plotly_dark",
            margin=dict(l=0, r=0, t=40, b=0),
            height=600 if show_rsi else 500
        )
        
        # Formato de Fecha Eje X
        if "h" in timeframe_interval or "m" in timeframe_interval:
             fig.update_xaxes(tickformat="%d %b, %H:%M") 

        # Ocultar fines de semana (Global)
        if "BTC" not in ticker and "ETH" not in ticker and "SOL" not in ticker and "XRP" not in ticker:
             if timeframe_interval == "1d":
                fig.update_xaxes(rangebreaks=[dict(bounds=["sat", "mon"])])
        
        return fig, analysis_data
        
    except Exception as e:
        st.error(f"Error generando gráfico: {e}")
        return None, None

def fetch_rss_news():
    feeds = [
        {"url": "https://es.cointelegraph.com/rss", "source": "CoinTelegraph"},
        {"url": "https://es.investing.com/rss/news.rss", "source": "Investing.com"},
        {"url": "https://es.investing.com/rss/news_287.rss", "source": "Inv. Política"} # Geopolítica
    ]
    
    all_news = []
    
    for feed_info in feeds:
        try:
            feed = feedparser.parse(feed_info["url"])
            if not feed.entries:
                continue
                
            for entry in feed.entries[:8]: # Aumentado límite para más contexto
                published_time = entry.get('published_parsed', time.struct_time(time.localtime()))
                published_time = entry.get('published_parsed', time.struct_time(time.localtime()))
                
                raw_summary = entry.get('summary', '')
                raw_title = entry.get('title', 'Sin título')
                
                clean_summary = clean_html(raw_summary)
                clean_title = clean_html(raw_title)
                
                if len(clean_summary) > 200:
                    clean_summary = clean_summary[:200] + "..."
                
                score, sentiment_label, sentiment_color = get_sentiment(clean_title)
                category_label, category_color = categorize_news(clean_title, clean_summary, feed_info["source"])

                all_news.append({
                    "source": feed_info["source"],
                    "title": clean_title,
                    "link": entry.get('link', '#'),
                    "published_parsed": published_time,
                    "summary": clean_summary,
                    "sentiment_label": sentiment_label,
                    "sentiment_color": sentiment_color,
                    "category_label": category_label,
                    "category_color": category_color
                })
        except Exception as e:
            st.error(f"Error cargando feed de {feed_info['source']}")
    
    all_news.sort(key=lambda x: x['published_parsed'], reverse=True)
    return all_news

def format_ticker(col, label, data, is_crypto=False, decimal_places=2):
    with col:
        if data:
            price, change = data
            if is_crypto:
                fmt = f"{price:,.0f}" # Cryptos often integer or few decimals
            elif decimal_places == 5:
                fmt = f"{price:,.5f}"
            elif decimal_places == 3:
                fmt = f"{price:,.3f}"
            else:
                fmt = f"{price:,.2f}"
            col.metric(label=label, value=fmt, delta=f"{change:.2f}%")
        else:
            col.metric(label=label, value="N/A", delta=None)

def main():
    
    # 1. HEADER & RELOJES MUNDIALES (PHASE 9 & 12 & 13)
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;700&display=swap');
        
        /* 1. FONDO INMERSIVO (Phase 13) */
        .stApp {
            background: radial-gradient(circle at center, #1a1c24 0%, #000000 100%);
            background-attachment: fixed;
        }

        /* 2. GLASSMORPHISM CORE */
        .glass-card, div[data-testid="stMetric"], .news-card {
            background-color: rgba(255, 255, 255, 0.05) !important;
            border: 1px solid rgba(255, 255, 255, 0.1) !important;
            border-radius: 10px !important;
            padding: 15px;
            backdrop-filter: blur(8px);
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
        }
        
        /* Ajuste específico para Métricas Nativas */
        div[data-testid="stMetric"] {
            padding: 10px;
            text-align: center;
        }
        div[data-testid="stMetric"] label {
            color: #b0bec5 !important; /* Color etiqueta suave */
        }
        
        /* LOGO STYLES */
        .logo-container {
            text-align: center;
            margin-bottom: 30px;
            margin-top: 10px;
        }
        .main-logo {
            font-family: 'Poppins', sans-serif;
            font-size: 3.5rem;
            font-weight: 700;
            line-height: 1.2;
            text-transform: uppercase;
            letter-spacing: 2px;
            text-shadow: 0 0 20px rgba(38, 166, 154, 0.3); /* Glow sutil */
        }
        .zen-text { color: #26a69a; } 
        .trader-text { color: #ffb74d; }
        .tagline {
            font-family: 'Poppins', sans-serif;
            font-size: 1.1rem;
            font-weight: 300;
            color: #b0bec5; 
            margin-top: -10px;
            letter-spacing: 1px;
        }
        .sentinel-highlight { color: #ffffff; font-weight: 700; }
        
        /* NEWS CARD Styles overrides */
        .news-card {
            margin-bottom: 15px;
            transition: transform 0.2s;
        }
        .news-card:hover {
            transform: translateY(-2px);
            border-color: rgba(255, 255, 255, 0.3) !important;
        }
        </style>

        <div class="logo-container">
            <div class="main-logo">
                <span class="zen-text">ZEN</span><span class="trader-text">TRADER</span>
            </div>
            <div class="tagline">
                Operativa Consciente | <span class="sentinel-highlight">SENTINEL</span> System
            </div>
        </div>
    """, unsafe_allow_html=True)
    st.divider()
    
    # Relojes (Diseño Digital Cards - Glass)
    col_clock1, col_clock2, col_clock3 = st.columns(3)
    
    # Zonas Horarias
    tz_ny = pytz.timezone('America/New_York')
    tz_london = pytz.timezone('Europe/London')
    tz_tokyo = pytz.timezone('Asia/Tokyo')
    
    def clock_card(emoji, city, timezone):
        time_str = datetime.now(timezone).strftime('%H:%M')
        # Usamos la clase glass-card definida en CSS
        return f"""
        <div class="glass-card" style="text-align: center; margin-bottom: 10px;">
            <div style="font-size: 0.9em; color: #bbb; margin-bottom: 2px;">{emoji} {city}</div>
            <div style="font-size: 1.8em; font-weight: bold; color: #fff; font-family: 'Courier New', monospace;">{time_str}</div>
        </div>
        """

    with col_clock1:
        st.markdown(clock_card("🇺🇸", "Wall Street", tz_ny), unsafe_allow_html=True)
    with col_clock2:
        st.markdown(clock_card("🇬🇧", "Londres", tz_london), unsafe_allow_html=True)
    with col_clock3:
        st.markdown(clock_card("🇯🇵", "Tokio", tz_tokyo), unsafe_allow_html=True)
    
    st.markdown("---") # Divider estilo markdown
    
    # --- MÓDULO SIDEBAR: SALUD INTEGRAL (PHASE 5) ---
    st.sidebar.header("🛡️ Protocolo Biofeedback")
    st.sidebar.markdown("Diagnóstico de Estado Operativo")
    
    # Inputs (Valores por defecto estrictos para reiniciar al usuario)
    mood = st.sidebar.slider("1. Ánimo / Confianza (1-10)", 1, 10, 1) # Default 1 (Bajo)
    sleep = st.sidebar.slider("2. Horas de Sueño", 0, 12, 0) # Default 0 (Zombi)
    stress = st.sidebar.slider("3. Nivel de Estrés Percibido (1-10)", 1, 10, 10) # Default 10 (Pánico)
    
    # Opciones reordenadas para que el default sea "negativo" asi el usuario debe cambiarlo
    meal_options = ["Ayuno / Café (Riesgo)", "Pesada/Grasa", "Azúcar/Procesados", "Normal", "Ligera/Sana"]
    meal = st.sidebar.selectbox("4. Última Comida", meal_options,  index=0, help="El ayuno prolongado sin electrolitos o comidas pesadas afectan tu cognición.")
    
    nature = st.sidebar.checkbox("5. ¿Contacto con Naturaleza/Deporte hoy?", value=False)
    
    # Cálculo Zen Score
    zen_score, reasons = calculate_zen_score(mood, sleep, stress, meal, nature)
    
    # Visualización Score Sidebar
    st.sidebar.divider()
    st.sidebar.metric("ZEN SCORE", f"{zen_score}/100")
    
    st.sidebar.info("🧠 **Recuerda:** El 90% del trading es mental. Si tu cortisol está alto, tu visión de mercado se nubla. Respeta tu biología.")
    

    


    # --- CONTEXTO DE SESIÓN (PHASE 21) ---
    st.sidebar.markdown("---")
    
    # Lógica de Hora UTC
    utc_now = datetime.now(pytz.utc).hour
    
    session_text = ""
    if 13 <= utc_now < 16:
        session_text = "🔥 ZONA DE FUEGO (Londres + NY). Peligro y Oportunidad."
    elif 8 <= utc_now < 16:
        session_text = "🟢 Sesión Europea (Volumen Alto)"
    elif 13 <= utc_now < 21:
        session_text = "🟢 Sesión Americana (Volatilidad Máxima)"
    else:
        session_text = "🟡 Sesión Asiática (Movimiento Lento)"
        
    st.sidebar.info(f"🌍 **Contexto:** {session_text}")
    
    # --- CONFIGURACIÓN DE CUENTA (Phase 27) ---
    with st.sidebar.expander("⚙️ Gestión de Capital", expanded=False):
        account_capital = st.number_input("Capital Total ($)", value=1000.0, step=100.0)
        max_risk_pct = st.number_input("Riesgo Máximo por Op. (%)", value=1.0, step=0.1, max_value=5.0)
        
    # --- VOZ DE MANDO (Phase 32) ---
    st.sidebar.checkbox("🎤 Activar Asesor de Voz", value=False, key="voice_active")

    # --- RADAR DE EVENTOS (Phase 30) ---
    with st.sidebar.expander("📅 Radar Económico", expanded=False):
        eventos = obtener_calendario_economico()
        if eventos:
            for e in eventos:
                st.markdown(f"**{e.title}**")
                # Alerta simplificada por palabras clave
                if any(x in e.title.lower() for x in ["pib", "ipc", "fed", "bce", "empleo", "tasa", "rate"]):
                    st.caption("⚠️ **ALTO IMPACTO**")
                st.divider()
        else:
            st.write("Sin datos.")

    # Regla de Pase: Score >= 70
    if zen_score < 70:
        mostrar_bloqueo(zen_score, reasons)
    else:
        # Pasamos parámetros de riesgo y niveles al dashboard
        mostrar_dashboard(zen_score, reasons, meal, account_capital, max_risk_pct)

def mostrar_bloqueo(score, reasons):
    st.markdown("---")
    st.error(f"🛑 ZONA DE PELIGRO: Zen Score {score}/100 🛑")
    
    st.markdown(f"""
        <div class='warning-box'>
            <h3>🚫 ACCESO DENEGADO AL MERCADO</h3>
            <p>Tu estado psicofisiológico actual presenta riesgos inaceptables para tu capital.</p>
        </div>
    """, unsafe_allow_html=True)
    
    st.subheader("Diagnóstico del Guardián:")
    for r in reasons:
        st.write(r)
        
    st.markdown("### 🧘 Recomendación Prescriptiva:")
    st.info("No operes ahora. Tu cerebro necesita un 'Hard Reset'. Sal a caminar a la playa o al bosque, respira aire limpio y vuelve mañana. El mercado te esperará.")

def mostrar_dashboard(score, reasons, meal, account_capital, max_risk_pct):
    st.markdown("---")
    
    # Mensaje positivo
    st.markdown(f"""
        <div class='success-box'>
            <h3>✅ SISTEMAS APROBADOS (Score: {score})</h3>
            <p>Estás en equilibrio. Recuerda: el trading es disciplina, no azar. Buena sesión.</p>
        </div>
    """, unsafe_allow_html=True)
    
    # Feedback Especial de Alimentación
    if meal in ["Pesada/Grasa", "Azúcar/Procesados"]:
        st.warning("⚠️ ALERTA BIOLÓGICA: Tu alimentación reciente puede causar somnolencia o picos de insulina. Mantente alerta a la fatiga en 30 min.")
    elif meal == "Ligera/Sana":
        st.success("🍏 Combustible limpio confirmado. Tu cerebro está optimizado.")
    
    # Mostrar bonificaciones si las hay
    if reasons:
        with st.expander("Factores de Impacto"):
            for r in reasons:
                st.write(r)
    
    st.divider()
    
    # --- BARRA DE PRECIOS EN VIVO (Global) ---
    market_data = get_market_prices()
    
    # --- PESTAÑAS PRINCIPALES (Phase 25) ---
    tab_operativa, tab_analisis, tab_wiki = st.tabs(["🚀 Sala de Operaciones", "📊 Mi Rendimiento", "📚 Códice del Conocimiento"])

    # --- PESTAÑA 1: SALA DE OPERACIONES ---
    with tab_operativa:
        if market_data:
            st.subheader("📡 Inteligencia de Mercado")
        
            # 1. Ticker Tape (Precios en vivo) - Reorganizado en 3 Filas x 4 Columnas (Simetría)
            prices = market_data
            
            # FILA 1: DINERO & METALES (Macro)
            st.caption("🌐 Macroeconomía & Divisas")
            col_macro1, col_macro2, col_macro3, col_macro4 = st.columns(4)
            format_ticker(col_macro1, "Índice Dólar", prices.get("Índice Dólar"), decimal_places=3)
            format_ticker(col_macro2, "EUR/USD", prices.get("EUR/USD"), decimal_places=5)
            format_ticker(col_macro3, "USD/JPY", prices.get("USD/JPY"), decimal_places=3)
            format_ticker(col_macro4, "Oro", prices.get("Oro"))
            
            # FILA 2: ECONOMÍA & RIESGO
            st.caption("🏢 Mercado Tradicional & Miedo")
            col_trad1, col_trad2, col_trad3, col_trad4 = st.columns(4)
            format_ticker(col_trad1, "S&P 500", prices.get("S&P 500"))
            format_ticker(col_trad2, "Nasdaq", prices.get("Nasdaq"))
            format_ticker(col_trad3, "Nvidia", prices.get("Nvidia"))
            format_ticker(col_trad4, "VIX (Miedo)", prices.get("VIX (Miedo)")) # Volatilidad
    
            # FILA 3: ECOSISTEMA CRIPTO (Elite 4)
            st.caption("🚀 Cripto Elite")
            col_crip1, col_crip2, col_crip3, col_crip4 = st.columns(4)
            format_ticker(col_crip1, "Bitcoin", prices.get("Bitcoin"), is_crypto=True)
            format_ticker(col_crip2, "Ethereum", prices.get("Ethereum"), is_crypto=True)
            format_ticker(col_crip3, "Solana", prices.get("Solana"), is_crypto=True)
            format_ticker(col_crip4, "XRP", prices.get("XRP"), decimal_places=4) # XRP suele tener decimales
            
            st.divider()
    
        # --- GRÁFICO INTERACTIVO ---
        st.subheader("📊 Análisis Técnico")
        
        chart_options = {
            "Bitcoin (BTC-USD)": "BTC-USD",
            "Ethereum (ETH-USD)": "ETH-USD",
            "Solana (SOL-USD)": "SOL-USD",
            "XRP (XRP-USD)": "XRP-USD",
            "Oro (GC-F)": "GC=F",
            "EUR/USD": "EURUSD=X",
            "S&P 500": "^GSPC",
            "Nvidia": "NVDA",
            "Índice Dólar (DXY)": "DX-Y.NYB",
            "USD/JPY": "JPY=X",
            "VIX (Volatilidad)": "^VIX"
        }
        
        # AQUI AGREGAMOS LA KEY PARA SESSION STATE
        col_asset, col_tf = st.columns([2, 1])
        with col_asset:
            selected_asset = st.selectbox("Selecciona Activo para Análisis:", list(chart_options.keys()), key='selected_asset_key')
        with col_tf:
            tf_label = st.selectbox("Temporalidad:", ["1 Hora (Intradía)", "1 Día (Swing)", "1 Semana (Macro)"], index=1)
        
        # Mapeo de configuración
        if "Hora" in tf_label:
            tf_interval = "1h"
            tf_period = "1mo"
        elif "Semana" in tf_label:
            tf_interval = "1wk"
            tf_period = "2y"
        else:
            tf_interval = "1d"
            tf_period = "1y" # 1 año para Swing
        
        # Checkboxes para indicadores técnicos
        col_ind1, col_ind2 = st.columns(2)
        with col_ind1:
            show_bb = st.checkbox("Mostrar Bandas de Bollinger")
            # PIVOTES ELIMINADOS DE UI
        with col_ind2:
            show_rsi = st.checkbox("Mostrar RSI (Índice de Fuerza Relativa)")
        
        if selected_asset:
            ticker = chart_options[selected_asset]
            with st.spinner(f'Cargando gráfico de {selected_asset}...'):
                # Pasamos los niveles de riesgo y técnicos al gráfico
                fig, analysis = create_chart(ticker, selected_asset, tf_interval, tf_period, show_rsi, show_bb)
                
                if fig:
                    st.plotly_chart(fig, use_container_width=True)
                    
                # MENTOR IA (Phase 20)
                if analysis:
                    display_mentor_analysis(analysis, selected_asset, account_capital, max_risk_pct)
        
        st.divider()
    
        st.divider()
    
        # --- RADAR TÁCTICO (SCANNER) (Phase 18) ---
        with st.expander("📡 Radar Táctico: Escáner de Oportunidades (12 Activos)", expanded=True):
            st.caption("Análisis automático de RSI, Tendencia y Volatilidad en tiempo real.")
            with st.spinner("Escaneando mercado..."):
                styled_df = get_styled_scanner()
                if styled_df is not None:
                    st.dataframe(styled_df, use_container_width=True)
                else:
                    st.warning("No se pudo escanear el mercado.")
    
        # --- MATRIZ DE SINERGIA (Phase 24) ---
        with st.expander("🕸️ Matriz de Sinergia (Conexiones Ocultas)", expanded=False):
            st.caption("Mapa de calor que revela qué activos son aliados y cuáles son enemigos.")
            with st.spinner("Calculando correlaciones matemáticas..."):
                corr_matrix = get_correlation_matrix()
                if corr_matrix is not None:
                    st.dataframe(style_correlation(corr_matrix), use_container_width=True)
                    st.info("💡 **Cómo leer esto:** Rojo Intenso (-1.0) = Enemigos (Inversa). Verde Intenso (+1.0) = Aliados (Mismo movimiento). Gris = Sin relación.")
                else:
                    st.warning("No hay suficientes datos para la matriz.")
    
        # --- NOTICIAS ---
        st.subheader("📰 Inteligencia de Mercado en Tiempo Real")
        
        with st.spinner('Procesando noticias + Análisis NLP + Categorización...'):
            noticias = fetch_rss_news()
        
        if noticias:
            col_izq, col_der = st.columns(2)
            for i, noticia in enumerate(noticias):
                target_col = col_izq if i % 2 == 0 else col_der
                with target_col:
                    st.markdown(f"""
                    <div class='news-card'>
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <div>
                               <span class='category-badge' style='background-color: {noticia['category_color']}'>{noticia['category_label']}</span>
                               <span class='news-source'>{noticia['source']}</span>
                            </div>
                            <span class='sentiment-badge' style='background-color: {noticia['sentiment_color']}'>{noticia['sentiment_label']}</span>
                        </div>
                        <h4 style="margin-top: 10px;">{noticia['title']}</h4>
                        <div style='margin-bottom: 10px; color: #ccc;'>{noticia['summary']}</div>
                        <a href="{noticia['link']}" target="_blank" style="color: #4caf50; text-decoration: none; font-weight: bold;">🔗 Leer noticia completa</a>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.warning("No se pudieron cargar las noticias.")

    # --- PESTAÑA 2: MI RENDIMIENTO (Bitácora) ---
    with tab_analisis:
        st.header("📊 Mi Rendimiento")
        st.write("Analiza tu progreso y psicología.")
        
        # --- BITÁCORA DE TRADING (Journaling) - Phase 14 ---
        st.subheader("📜 Bitácora de Sesión")
        
        with st.expander("📝 Escribir nueva entrada en el Diario", expanded=True):
            journal_entry = st.text_area("Reflexión del Trader:", placeholder="¿Qué aprendí hoy? ¿Cómo gestioné mis emociones? ¿Seguí mi plan?", height=150)
            
            if st.button("💾 Guardar en Historial"):
                if journal_entry:
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    # Recuperar activo
                    active_asset = st.session_state.get('selected_asset_key', 'Ninguno')
                    
                    # Guardar en CSV
                    df_entry = pd.DataFrame([{
                        "Fecha": timestamp,
                        "ZenScore": score,
                        "Activo": active_asset,
                        "Nota": journal_entry
                    }])
                    
                    file_path = "trading_journal.csv"
                    # Append si existe, write si no
                    write_header = not pd.io.common.file_exists(file_path)
                    df_entry.to_csv(file_path, mode='a', header=write_header, index=False)
                    
                    st.success("✅ Entrada guardada en la memoria del sistema.")
                else:
                    st.warning("⚠️ La bitácora está vacía. Escribe algo antes de guardar.")

        # Visualizar historial (Simple)
        file_path = "trading_journal.csv"
        if os.path.exists(file_path):
            st.divider()
            st.write("### Historial Reciente")
            try:
                df_hist = pd.read_csv(file_path)
                st.dataframe(df_hist.sort_values(by="Fecha", ascending=False), use_container_width=True)
            except Exception:
                st.error("Error leyendo historial.")

    # --- PESTAÑA 3: CÓDICE DEL CONOCIMIENTO (Wiki Phase 26) ---
    with tab_wiki:
        st.header("📚 Códice del Conocimiento: La Sabiduría del Veterano")
        st.write("La información es poder. Aquí reside la diferencia entre un apostador y un profesional.")
        st.divider()
        
        col_w1, col_w2, col_w3 = st.columns(3)
        
        # --- COLUMNA 1: LOS 10 MANDAMIENTOS ---
        with col_w1:
            st.subheader("📜 Leyes Inquebrantables")
            with st.expander("Los 10 Mandamientos del Trader", expanded=True):
                st.error("1. Preservar el Capital es la Prioridad #1.") 
                st.caption("Si pierdes tus fichas, te echan del casino. No busques ganar, busca no morir.")
                
                st.warning("2. Nunca corras detrás del precio.")
                st.caption("Si el tren se fue, déjalo ir. Siempre habrá otro tren (setup). La paciencia paga.")
                
                st.info("3. Corta las pérdidas rápido, deja correr las ganancias.")
                st.caption("El error novato es hacer lo contrario: aguantar rojos esperando un milagro y cortar verdes por miedo.")
                
                st.error("4. El Mercado siempre tiene la razón.")
                st.caption("Tu opinión, tu ego y tu análisis no valen nada frente a la acción del precio.")
                
                st.error("5. No operes por venganza.")
                st.caption("Si perdiste, acepta la derrota. Intentar recuperar 'lo tuyo' solo acelerará tu ruina.")
                
                st.success("6. Planifica tu operación y opera tu plan.")
                st.caption("Entrada, Salida y Stop definidos ANTES de dar click. Sin plan, eres liquidez.")
                
                st.info("7. La paciencia es el activo más valioso.")
                st.caption("Los francotiradores esperan días por un solo disparo. Los amateurs disparan a todo lo que se mueve.")
                
                st.warning("8. No arriesgues más del 1-2% por operación.")
                st.caption("La matemática de la ruina es real. Una mala racha no debe borrarte del mapa.")
                
                st.success("9. La tendencia es tu amiga hasta que se dobla.")
                st.caption("No intentes ser el héroe que adivina el techo. Fluye con el río.")
                
                st.info("10. Descansa. El trading es un maratón.")
                st.caption("Tu cerebro fatigado comete errores caros. Duerme, come bien y vive.")

        # --- COLUMNA 2: GLOSARIO TÁCTICO ---
        with col_w2:
            st.subheader("🧠 Glosario Táctico")
            with st.expander("Diccionario de Indicadores", expanded=True):
                st.markdown("### 🏎️ RSI (El Velocímetro)")
                st.info("Mide la velocidad del precio. **>70 (Sobrecompra):** El motor va muy forzado, peligro de corrección. **<30 (Sobreventa):** El precio ha caído demasiado rápido, posible rebote.")
                
                st.markdown("### 🌊 MACD (La Brújula)")
                st.info("Mide el momentum (inercia). Cuando las líneas se cruzan, indican cambio de marea. Útil para confirmar si el movimiento tiene fuerza real.")
                
                st.markdown("### 🎢 Bandas Bollinger (La Carretera)")
                st.warning("El precio suele moverse dentro de estas bandas el 95% del tiempo. Si se sale, es un evento extremo (euforia o pánico) que suele revertirse hacia la media.")
                
                st.markdown("### 🧨 ATR (El Clima)")
                st.success("Mide la volatilidad real en dólares. Si el ATR es alto, hay tormenta (velas grandes). Úsalo para poner tu Stop Loss fuera del 'ruido' normal (2 veces el ATR).")

        # --- COLUMNA 3: LECTURA DE VELAS ---
        with col_w3:
            st.subheader("🕯️ Lectura de Velas")
            with st.expander("Patrones de Poder", expanded=True):
                st.markdown("### 🔨 El Martillo (Hammer)")
                st.success("**Señal Alcista:** Sombra larga abajo, cuerpo pequeño arriba. Significa que los vendedores intentaron hundir el precio, pero los compradores lo rechazaron con fuerza.")
                
                st.markdown("### 💫 Doji (Indecisión)")
                st.warning("**Señal Neutra/Giro:** Una cruz perfecta. Apertura y cierre iguales. Guerra equilibrada entre toros y osos. Precede a movimientos violentos.")
                
                st.markdown("### 🐋 Envolvente (Engulfing)")
                st.error("**Señal de Giro:** Una vela grande 'se come' completamente a la pequeña anterior. Indica que el control ha cambiado de manos drásticamente.")

    # FOOTER MANIFIESTO (Fase 11 & 14)
    st.divider()

    # FOOTER MANIFIESTO (Fase 11 & 14)
    st.markdown("""
        <div style="text-align: center; color: #666; font-size: 0.8em; margin-top: 40px; font-style: italic;">
            "En un mundo globalizado, la información es poder y el equilibrio es control. Trabajamos para ser mejores y ayudar a nuestros pares. Nadie está solo."
            <br><br>
            <strong>"El que no conoce su pasado está condenado a repetirlo. Tu mente es tu mayor activo."</strong>
            <br><br>
            <strong>ZenTrader Sentinel v1.1 - Phase 14</strong>
        </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
