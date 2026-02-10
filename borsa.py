import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import datetime

# Otomatik yenileme
try:
    from streamlit_autorefresh import st_autorefresh
except ImportError:
    st_autorefresh = None

# --- 1. SİTE AYARLARI ---
st.set_page_config(page_title="Raffık Finans v3.2", layout="wide", page_icon="🦅")

if st_autorefresh:
    st_autorefresh(interval=60000, key="fiyat_yenileme")

# --- SESSION STATE (HAFIZA) AYARI ---
# Tıklanan hisseyi hafızada tutmak için gerekli
if 'secilen_kod' not in st.session_state:
    st.session_state.secilen_kod = "GC=F" # Varsayılan: Gram Altın

st.markdown("""
<style>
    .main { background-color: #0e1117; }
    h1 { color: #ffd700; font-family: 'Trebuchet MS', sans-serif; }
    div[data-testid="stMetric"] { background-color: #1f2937; border: 1px solid #374151; padding: 10px; border-radius: 10px; }
    
    /* Yan Menü Butonlarını Liste Gibi Gösterme */
    div.stButton > button {
        width: 100%;
        text-align: left;
        border: 1px solid #374151;
        background-color: #1f2937;
        color: white;
        margin-bottom: 5px;
        display: flex;
        justify-content: space-between;
    }
    div.stButton > button:hover {
        border-color: #ffd700;
        color: #ffd700;
    }
    div.stButton > button:focus {
        border-color: #ffd700;
        box-shadow: none;
    }
</style>
""", unsafe_allow_html=True)

# --- BAŞLIK ---
col_logo, col_title = st.columns([1, 8])
with col_logo:
    st.image("https://cdn-icons-png.flaticon.com/512/3310/3310748.png", width=70)
with col_title:
    st.title("RAFFIK FİNANS: CANLI BORSA")
    st.caption(f"🔴 Tıklanabilir Liste Aktif | Son Güncelleme: {datetime.datetime.now().strftime('%H:%M:%S')}")
st.markdown("---")

# --- VARLIK LİSTESİ ---
HAM_LISTE = [
    "GC=F", "SI=F", "USDTRY=X",
    "THYAO.IS", "ASELS.IS", "BIMAS.IS", "EREGL.IS", "TUPRS.IS", 
    "AKBNK.IS", "GARAN.IS", "YKBNK.IS", "ISCTR.IS", "SAHOL.IS",
    "FROTO.IS", "TOASO.IS", "KCHOL.IS", "SASA.IS", "HEKTS.IS",
    "SISE.IS", "PETKM.IS", "PGSUS.IS", "ASTOR.IS", "KONTR.IS",
    "ENJSA.IS", "ALARK.IS", "ODAS.IS", "KOZAL.IS", "KRDMD.IS",
    "ARCLK.IS", "VESTL.IS", "EUPWR.IS", "CWENE.IS", "SMRTG.IS"
]

ISIM_SOZLUGU = {
    "GC=F": "GRAM ALTIN", "SI=F": "GRAM GÜMÜŞ", "USDTRY=X": "DOLAR/TL"
}

# --- TOPLU VERİ ÇEKME ---
@st.cache_data(ttl=60)
def liste_ozeti_getir(semboller):
    string_list = " ".join(semboller)
    try:
        data = yf.download(string_list, period="5d", group_by='ticker', progress=False)
        ozet_sozlugu = {}
        try:
            usd_change = 0
            usd_df = data["USDTRY=X"]
            if not usd_df.empty:
                last_usd = usd_df['Close'].dropna().iloc[-1]
                prev_usd = usd_df['Close'].dropna().iloc[-2]
                usd_change = ((last_usd - prev_usd) / prev_usd)
        except: usd_change = 0

        for s in semboller:
            try:
                df = data[s]
                if df.empty: continue
                closes = df['Close'].dropna()
                if len(closes) < 2: continue
                son_fiyat = closes.iloc[-1]
                onceki_fiyat = closes.iloc[-2]
                degisim = ((son_fiyat - onceki_fiyat) / onceki_fiyat)
                if s in ["GC=F", "SI=F"]:
                    degisim = (1 + degisim) * (1 + usd_change) - 1
                ozet_sozlugu[s] = degisim
            except: ozet_sozlugu[s] = 0.0
        return ozet_sozlugu
    except: return {}

# --- YAN MENÜ: TIKLANABİLİR LİSTE ---
st.sidebar.markdown("### 🦅 Piyasa Özeti")
st.sidebar.info("Detaylar için hisseye tıklayın 👇")

degisimler = liste_ozeti_getir(HAM_LISTE)

# Listeyi Sırala
def siralama_anahtari(kod):
    return ISIM_SOZLUGU.get(kod, kod.replace(".IS", ""))
sirali_liste = sorted(HAM_LISTE, key=siralama_anahtari)

# BUTON DÖNGÜSÜ
for kod in sirali_liste:
    ad = ISIM_SOZLUGU.get(kod, kod.replace(".IS", ""))
    yuzde = degisimler.get(kod, 0.0) * 100
    
    # Görsel İkonlar ve Format
    if yuzde > 0:
        label = f"{ad}  🟢  +%{yuzde:.2f}"
    elif yuzde < 0:
        label = f"{ad}  🔴  -%{abs(yuzde):.2f}"
    else:
        label = f"{ad}  ⚪  %0.00"
    
    # AKTİF BUTON RENGİ AYARI (Seçiliyse farklı görünsün)
    tip = "primary" if st.session_state.secilen_kod == kod else "secondary"
    
    # TIKLANABİLİR BUTON (Tam genişlikte)
    if st.sidebar.button(label, key=kod, use_container_width=True, type=tip):
        st.session_state.secilen_kod = kod # Hafızayı güncelle
        st.rerun() # Sayfayı yenile ki sağ taraf güncellensin

# --- SAĞ TARAF: DETAY EKRANI ---
st.sidebar.markdown("---")
# Detay ayarları
analiz_tipi = st.sidebar.radio("Para Birimi", ["TL (₺)", "Dolar ($)"])
periyot = st.sidebar.select_slider("Geçmiş", options=["1mo", "3mo", "1y", "5y"], value="1y")

# --- DETAY VERİ MOTORU ---
@st.cache_data(ttl=60)
def detay_veri_getir(sembol, tip, zaman):
    try:
        df = yf.Ticker(sembol).history(period=zaman)
        if df.empty: return pd.DataFrame()
        df.index = df.index.tz_localize(None)

        if sembol in ["GC=F", "SI=F"]:
            if tip == "TL (₺)":
                usd = yf.Ticker("USDTRY=X").history(period=zaman)
                usd.index = usd.index.tz_localize(None)
                df = df.join(usd['Close'].rename("kur"), how='left').ffill().bfill()
                for c in ['Open', 'High', 'Low', 'Close']:
                    df[c] = (df[c] * df['kur']) / 31.1034768
            else:
                for c in ['Open', 'High', 'Low', 'Close']:
                    df[c] = df[c] / 31.1034768
        elif tip == "Dolar ($)" and "IS" in sembol:
             usd = yf.Ticker("USDTRY=X").history(period=zaman)
             usd.index = usd.index.tz_localize(None)
             df = df.join(usd['Close'].rename("kur"), how='left').ffill().bfill()
             for c in ['Open', 'High', 'Low', 'Close']:
                    df[c] = df[c] / df['kur']
        return df
    except: return pd.DataFrame()

# Seçilen hisseyi hafızadan al
secilen_ad = ISIM_SOZLUGU.get(st.session_state.secilen_kod, st.session_state.secilen_kod.replace(".IS", ""))
st.subheader(f"📊 {secilen_ad} Analizi")

df = detay_veri_getir(st.session_state.secilen_kod, analiz_tipi, periyot)

if not df.empty:
    son = df['Close'].iloc[-1]
    onceki = df['Close'].iloc[-2]
    degisim_val = ((son - onceki) / onceki) * 100
    simge = "₺" if analiz_tipi == "TL (₺)" else "$"
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Son Fiyat", f"{son:.2f} {simge}", f"%{degisim_val:.2f}")
    
    en_yuksek = df['High'].max()
    en_dusuk = df['Low'].min()
    col2.metric("Dönem En Yüksek", f"{en_yuksek:.2f} {simge}")
    col3.metric("Dönem En Düşük", f"{en_dusuk:.2f} {simge}")
    
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_width=[0.2, 0.7])
    fig.add_trace(go.Candlestick(
        x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'],
        name="Fiyat"
    ), row=1, col=1)
    fig.add_trace(go.Bar(x=df.index, y=df['Volume'], name="Hacim", marker_color='rgba(100, 100, 255, 0.5)'), row=2, col=1)
    fig.update_layout(template="plotly_dark", height=600, xaxis_rangeslider_visible=False, margin=dict(l=10, r=10, t=10, b=10))
    st.plotly_chart(fig, use_container_width=True)
else:
    st.error("Veri yüklenemedi. Bağlantı hatası olabilir.")
