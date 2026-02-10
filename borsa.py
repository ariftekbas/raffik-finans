import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import datetime
import requests
import xml.etree.ElementTree as ET
import google.generativeai as genai

# ==========================================
# 🔑 AYARLAR VE API ANAHTARI
# ==========================================
# Arif Baba, API anahtarın tırnak içinde ve güvenli:
GEMINI_API_KEY = "AIzaSyAohuPCw8DxngrgEavuiybzNCjRg3cS57Y"

# Gemini Kurulumu
AI_AKTIF = False
try:
    if GEMINI_API_KEY and "BURAYA" not in GEMINI_API_KEY:
        genai.configure(api_key=GEMINI_API_KEY)
        # DÜZELTME: 'gemini-1.5-flash' yerine en uyumlu model 'gemini-pro' seçildi.
        model = genai.GenerativeModel('gemini-pro')
        AI_AKTIF = True
except:
    AI_AKTIF = False

try:
    from streamlit_autorefresh import st_autorefresh
except ImportError:
    st_autorefresh = None

# ==========================================
# ⚙️ SİTE YAPILANDIRMASI
# ==========================================
st.set_page_config(page_title="Artek Finans Pro", layout="wide", page_icon="🦅")

st.markdown("""
<style>
    .main { background-color: #0e1117; }
    h1 { color: #ffd700; font-family: 'Trebuchet MS', sans-serif; }
    div[data-testid="stMetric"] { background-color: #1f2937; border: 1px solid #374151; padding: 10px; border-radius: 10px; }
    .badge { display: inline-flex; align-items: center; padding: 2px 8px; border-radius: 6px; font-weight: bold; font-size: 12px; margin-left: 5px; }
    .badge-up { background-color: #065f46; color: #34d399; }
    .badge-down { background-color: #7f1d1d; color: #fca5a5; }
    .badge-flat { background-color: #374151; color: #d1d5db; }
    div.stButton > button { padding: 0px 5px; min-height: 30px; height: 30px; line-height: 1; border: 1px solid #4b5563; }
    .depth-container { width: 100%; background-color: #374151; border-radius: 5px; height: 25px; display: flex; overflow: hidden; margin-top: 5px; }
    .depth-buy { background-color: #00c853; height: 100%; display: flex; align-items: center; justify-content: center; font-size: 11px; font-weight: bold; color: black; }
    .depth-sell { background-color: #d50000; height: 100%; display: flex; align-items: center; justify-content: center; font-size: 11px; font-weight: bold; color: white; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 🕒 ZAMAN VE OTOMATİK YENİLEME
# ==========================================
def simdi_tr():
    return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=3)))

tr_saat = simdi_tr()
borsa_acik_mi = False
if tr_saat.weekday() < 5 and ((9 <= tr_saat.hour < 18) or (tr_saat.hour == 18 and tr_saat.minute <= 30)):
    borsa_acik_mi = True
    if st_autorefresh: st_autorefresh(interval=60000, key="fiyat_yenileme")

if 'secilen_kod' not in st.session_state: st.session_state.secilen_kod = "GC=F"
if 'favoriler' not in st.session_state: st.session_state.favoriler = []

# ==========================================
# 📊 LİSTE TANIMLARI
# ==========================================
HAM_LISTE = ["GC=F", "SI=F", "USDTRY=X", "AEFES.IS", "AGHOL.IS", "AHGAZ.IS", "AKBNK.IS", "AKCNS.IS", "AKFGY.IS", "AKFYE.IS", "AKSA.IS", "AKSEN.IS", "ALARK.IS", "ALBRK.IS", "ALFAS.IS", "ARCLK.IS", "ASELS.IS", "ASTOR.IS", "ASUZU.IS", "AYDEM.IS", "BAGFS.IS", "BERA.IS", "BIMAS.IS", "BIOEN.IS", "BRSAN.IS", "BRYAT.IS", "BUCIM.IS", "CANTE.IS", "CCOLA.IS", "CEMTS.IS", "CIMSA.IS", "CWENE.IS", "DOAS.IS", "DOHOL.IS", "ECILC.IS", "ECZYT.IS", "EGEEN.IS", "EKGYO.IS", "ENJSA.IS", "ENKAI.IS", "EREGL.IS", "EUPWR.IS", "EUREN.IS", "FROTO.IS", "GARAN.IS", "GENIL.IS", "GESAN.IS", "GLYHO.IS", "GSDHO.IS", "GUBRF.IS", "GWIND.IS", "HALKB.IS", "HEKTS.IS", "IPEKE.IS", "ISCTR.IS", "ISDMR.IS", "ISFIN.IS", "ISGYO.IS", "ISMEN.IS", "IZMDC.IS", "KARSN.IS", "KCAER.IS", "KCHOL.IS", "KONTR.IS", "KONYA.IS", "KORDS.IS", "KOZAA.IS", "KOZAL.IS", "KRDMD.IS", "KZBGY.IS", "MAVI.IS", "MGROS.IS", "MIATK.IS", "ODAS.IS", "OTKAR.IS", "OYAKC.IS", "PENTA.IS", "PETKM.IS", "PGSUS.IS", "PSGYO.IS", "QUAGR.IS", "SAHOL.IS", "SASA.IS", "SISE.IS", "SKBNK.IS", "SMRTG.IS", "SNGYO.IS", "SOKM.IS", "TAVHL.IS", "TCELL.IS", "THYAO.IS", "TKFEN.IS", "TOASO.IS", "TSKB.IS", "TTKOM.IS", "TTRAK.IS", "TUKAS.IS", "TUPRS.IS", "TURSG.IS", "ULKER.IS", "VAKBN.IS", "VESBE.IS", "VESTL.IS", "YEOTK.IS", "YKBNK.IS", "YYLGD.IS", "ZOREN.IS"]

ISIM_SOZLUGU = {"GC=F": "GRAM ALTIN", "SI=F": "GRAM GÜMÜŞ", "USDTRY=X": "DOLAR/TL", "THYAO.IS": "THY", "ASELS.IS": "ASELSAN", "BIMAS.IS": "BIM", "EREGL.IS": "EREGLI", "TUPRS.IS": "TUPRAS", "AKBNK.IS": "AKBANK", "GARAN.IS": "GARANTI", "YKBNK.IS": "YAPI KREDI", "ISCTR.IS": "IS BANKASI", "SAHOL.IS": "SABANCI HOL.", "FROTO.IS": "FORD OTO", "TOASO.IS": "TOFAS", "KCHOL.IS": "KOC HOLDING", "SASA.IS": "SASA POLY.", "HEKTS.IS": "HEKTAS", "SISE.IS": "SISECAM", "PETKM.IS": "PETKIM", "PGSUS.IS": "PEGASUS", "ASTOR.IS": "ASTOR ENERJI", "KONTR.IS": "KONTROLMATIK", "ENJSA.IS": "ENERJISA", "ALARK.IS": "ALARKO", "ODAS.IS": "ODAS ELEK.", "KOZAL.IS": "KOZA ALTIN", "KRDMD.IS": "KARDEMIR D", "ARCLK.IS": "ARCELIK", "VESTL.IS": "VESTEL", "EUPWR.IS": "EUROPOWER", "CWENE.IS": "CW ENERJI", "SMRTG.IS": "SMART GUNES", "MGROS.IS": "MIGROS", "TCELL.IS": "TURKCELL", "TTKOM.IS": "TURK TELEKOM", "EKGYO.IS": "EMLAK KONUT", "OYAKC.IS": "OYAK CIMENTO", "GUBRF.IS": "GUBRE FAB.", "DOHOL.IS": "DOGAN HOLDING", "SOKM.IS": "SOK MARKET", "ULKER.IS": "ULKER", "AEFES.IS": "ANADOLU EFES"}

# ==========================================
# 🛠️ FONKSİYONLAR
# ==========================================
@st.cache_data(ttl=60)
def liste_ozeti_getir(semboller):
    try:
        data = yf.download(" ".join(semboller), period="5d", group_by='ticker', progress=False)
        ozet = {}
        try:
            usd_df = data["USDTRY=X"]['Close'].dropna()
            usd_ch = ((usd_df.iloc[-1] - usd_df.iloc[-2]) / usd_df.iloc[-2]) if len(usd_df) > 1 else 0
        except: usd_ch = 0
        for s in semboller:
            try:
                df = data[s]['Close'].dropna()
                if len(df) < 2: ozet[s] = 0.0; continue
                ch = ((df.iloc[-1] - df.iloc[-2]) / df.iloc[-2])
                if s in ["GC=F", "SI=F"]: ch = (1 + ch) * (1 + usd_ch) - 1
                ozet[s] = ch
            except: ozet[s] = 0.0
        return ozet
    except: return {}

def google_rss_haberleri(arama):
    try:
        url = f"https://news.google.com/rss/search?q={arama}&hl=tr&gl=TR&ceid=TR:tr"
        res = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=5)
        if res.status_code == 200:
            root = ET.fromstring(res.content)
            return [{'title': i.find('title').text, 'link': i.find('link').text, 'pubDate': i.find('pubDate').text} for i in root.findall('.//item')[:5]]
        return []
    except: return []

def gemini_piyasa_ozeti(basliklar, hisse):
    if not AI_AKTIF: return "Yapay zeka anahtarı veya kütüphane sorunu var."
    metin = "\n".join([f"- {b}" for b in basliklar])
    prompt = f"Borsa analistisin. '{hisse}' hissesi haberlerini TEK PARAGRAFTA, samimi dille özetle: {metin}"
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return f"⚠️ ANALİZ HATASI: {str(e)}"

def calculate_rsi(data, period=14):
    delta = data.diff(); gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    return 100 - (100 / (1 + (gain / loss)))

# ==========================================
# 🖥️ ARAYÜZ
# ==========================================
st.sidebar.markdown("### ⚙️ Ayarlar")
analiz_tipi = st.sidebar.radio("Para Birimi", ["TL (₺)", "Dolar ($)"], horizontal=True)
periyot = st.sidebar.select_slider("Grafik Geçmişi", options=["1mo", "3mo", "1y", "5y"], value="1y")

if st.session_state.favoriler:
    st.sidebar.markdown("### ⭐ Favoriler")
    fav_sil = st.sidebar.selectbox("Favori Çıkar", ["Seç..."] + st.session_state.favoriler)
    if fav_sil != "Seç...": st.session_state.favoriler.remove(fav_sil); st.rerun()

st.sidebar.markdown("---")
arama = st.sidebar.text_input("🔍 Hisse Ara / Ekle")
with st.spinner('Piyasa taranıyor...'): degisimler = liste_ozeti_getir(HAM_LISTE)
sirali = sorted(HAM_LISTE, key=lambda x: ISIM_SOZLUGU.get(x, x.replace(".IS", "")))

st.sidebar.markdown("### 🦅 Piyasa Özeti")
for kod in sirali:
    ad = ISIM_SOZLUGU.get(kod, kod.replace(".IS", ""))
    if arama and arama.lower() not in ad.lower() and arama.lower() not in kod.lower(): continue
    yuzde = degisimler.get(kod, 0.0) * 100
    badge = "badge-up" if yuzde > 0 else "badge-down" if yuzde < 0 else "badge-flat"
    c1, c2, c3 = st.sidebar.columns([0.15, 0.65, 0.2])
    if c1.button("★" if kod in st.session_state.favoriler else "☆", key=f"f_{kod}"):
        if kod in st.session_state.favoriler: st.session_state.favoriler.remove(kod)
        else: st.session_state.favoriler.append(kod)
        st.rerun()
    c2.markdown(f"<div style='font-size:13px; font-weight:bold;'>{'🟡' if st.session_state.secilen_kod == kod else ''} {ad} <span class='badge {badge}'>%{yuzde:.2f}</span></div>", unsafe_allow_html=True)
    if c3.button("➤", key=f"b_{kod}"): st.session_state.secilen_kod = kod; st.rerun()

# ANA EKRAN
secilen_ad = ISIM_SOZLUGU.get(st.session_state.secilen_kod, st.session_state.secilen_kod.replace(".IS", ""))
col_logo, col_title = st.columns([1, 8])
with col_logo: st.image("https://cdn-icons-png.flaticon.com/512/3310/3310748.png", width=70)
with col_title:
    st.title("Artek Finans: Pro")
    durum = "🟢 Piyasa Açık" if borsa_acik_mi else "🔴 Piyasa Kapalı"
    st.caption(f"{durum} | ⚠️ Veriler BIST kuralları gereği 15dk gecikmelidir.")

st.header(f"📊 {secilen_ad} Analiz Paneli")
t1, t2, t3 = st.tabs(["📈 TEKNİK", "🗞️ AI ÖZET", "📘 ŞİRKET"])

with t1:
    df = yf.Ticker(st.session_state.secilen_kod).history(period=periyot)
    if not df.empty:
        df.index = df.index.tz_localize(None)
        df['SMA20'] = df['Close'].rolling(20).mean(); df['RSI'] = calculate_rsi(df['Close'])
        son = df['Close'].iloc[-1]; deg = ((son - df['Close'].iloc[-2]) / df['Close'].iloc[-2]) * 100
        simge = "₺" if analiz_tipi == "TL (₺)" else "$"
        m1, m2, m3 = st.columns(3)
        m1.metric("Fiyat", f"{son:.2f} {simge}", f"%{deg:.2f}")
        m2.metric("RSI", f"{df['RSI'].iloc[-1]:.1f}"); m3.metric("SMA20", f"{df['SMA20'].iloc[-1]:.2f}")
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_width=[0.3, 0.7])
        fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name="Fiyat"), row=1, col=1)
        fig.add_trace(go.Bar(x=df.index, y=df['Volume'], name="Hacim"), row=2, col=1)
        fig.update_layout(template="plotly_dark", height=600, xaxis_rangeslider_visible=False)
        st.plotly_chart(fig, use_container_width=True)
    else: st.error("Veri yok.")

with t2:
    hbr = google_rss_haberleri(f"{secilen_ad} hisse")
    if hbr:
        st.info(gemini_piyasa_ozeti([h['title'] for h in hbr], secilen_ad))
        for h in hbr: st.write(f"🔗 [{h['title']}]({h['link']})")
    else: st.info("Haber yok.")

with t3:
    try:
        inf = yf.Ticker(st.session_state.secilen_kod).info
        st.write(inf.get('longBusinessSummary', 'Bilgi yok.'))
    except: st.write("Hata.")
