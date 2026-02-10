import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import datetime
# Otomatik yenileme (yüklüyse kullan, değilse geç)
try:
    from streamlit_autorefresh import st_autorefresh
except ImportError:
    st_autorefresh = None

# --- 1. SİTE AYARLARI ---
st.set_page_config(page_title="Raffık Finans v3.0", layout="wide", page_icon="🦅")

if st_autorefresh:
    st_autorefresh(interval=60000, key="fiyat_yenileme")

st.markdown("""
<style>
    .main { background-color: #0e1117; }
    h1 { color: #ffd700; font-family: 'Trebuchet MS', sans-serif; }
    div[data-testid="stMetric"] { background-color: #1f2937; border: 1px solid #374151; padding: 10px; border-radius: 10px; }
    /* Yan menüdeki radyo butonlarını biraz genişletelim */
    div.row-widget.stRadio > div { flex-direction: column; }
</style>
""", unsafe_allow_html=True)

# --- BAŞLIK ---
col_logo, col_title = st.columns([1, 8])
with col_logo:
    st.image("https://cdn-icons-png.flaticon.com/512/3310/3310748.png", width=70)
with col_title:
    st.title("RAFFIK FİNANS: CANLI BORSA")
    st.caption(f"🔴 Piyasa Özeti & Detaylı Analiz | Son Güncelleme: {datetime.datetime.now().strftime('%H:%M:%S')}")
st.markdown("---")

# --- VARLIK LİSTESİ ---
# Listeyi buraya tanımlıyoruz
HAM_LISTE = [
    "GC=F", "SI=F", "USDTRY=X", # Emtia ve Döviz
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

# --- TOPLU VERİ ÇEKME FONKSİYONU (LİSTE İÇİN) ---
@st.cache_data(ttl=60)
def liste_ozeti_getir(semboller):
    # Hepsini tek seferde çek (Hız için)
    string_list = " ".join(semboller)
    try:
        # Son 5 günün verisini alıyoruz ki hafta sonu olsa bile önceki kapanışı bulabilelim
        data = yf.download(string_list, period="5d", group_by='ticker', progress=False)
        
        ozet_sozlugu = {}
        
        # Dolar kurunu bul (Gram hesabı için lazım olabilir)
        try:
            usd_change = 0
            usd_df = data["USDTRY=X"]
            if not usd_df.empty:
                last_usd = usd_df['Close'].dropna().iloc[-1]
                prev_usd = usd_df['Close'].dropna().iloc[-2]
                usd_change = ((last_usd - prev_usd) / prev_usd)
        except:
            usd_change = 0

        for s in semboller:
            try:
                df = data[s]
                if df.empty: continue
                
                closes = df['Close'].dropna()
                if len(closes) < 2: continue
                
                son_fiyat = closes.iloc[-1]
                onceki_fiyat = closes.iloc[-2]
                degisim = ((son_fiyat - onceki_fiyat) / onceki_fiyat)
                
                # Altın/Gümüş için Gram değişimi yaklaşık hesabı (Basit Onz + Dolar değişimi)
                if s in ["GC=F", "SI=F"]:
                    degisim = (1 + degisim) * (1 + usd_change) - 1
                
                ozet_sozlugu[s] = degisim
            except:
                ozet_sozlugu[s] = 0.0
                
        return ozet_sozlugu
    except Exception as e:
        return {}

# --- YAN MENÜ OLUŞTURMA ---
st.sidebar.markdown("### 🦅 Hisse Listesi")

# 1. Önce verileri çekip yüzdeleri hesaplayalım
degisimler = liste_ozeti_getir(HAM_LISTE)

# 2. Listeyi Alfabetik Sırala (Önce isimler düzelsin diye sort key kullanıyoruz)
def siralama_anahtari(kod):
    return ISIM_SOZLUGU.get(kod, kod.replace(".IS", ""))

sirali_liste = sorted(HAM_LISTE, key=siralama_anahtari)

# 3. Görsel Seçenekleri Hazırla (🔴 🟢 ekle)
gorsel_secenekler = []
kod_haritasi = {} # Seçilen metinden gerçek kodu bulmak için

for kod in sirali_liste:
    ad = ISIM_SOZLUGU.get(kod, kod.replace(".IS", ""))
    yuzde = degisimler.get(kod, 0.0) * 100
    
    # Renk/Emoji Mantığı
    if yuzde > 0:
        emoji = "🟢"
        yuzde_metni = f"+%{yuzde:.2f}"
    elif yuzde < 0:
        emoji = "🔴"
        yuzde_metni = f"-%{abs(yuzde):.2f}"
    else:
        emoji = "⚪"
        yuzde_metni = "%0.00"
        
    gorunen_metin = f"{ad} {emoji} {yuzde_metni}"
    gorsel_secenekler.append(gorunen_metin)
    kod_haritasi[gorunen_metin] = kod

# 4. Radyo Butonu ile Seçim Yaptır
secilen_metin = st.sidebar.radio("Detayını Görmek İçin Seç:", options=gorsel_secenekler)
secilen_kod = kod_haritasi[secilen_metin]

# --- SEÇİLEN HİSSENİN DETAYLARI (SAĞ TARAF) ---
st.sidebar.markdown("---")
analiz_tipi = st.sidebar.radio("Para Birimi", ["TL (₺)", "Dolar ($)"])
periyot = st.sidebar.select_slider("Geçmiş", options=["1mo", "3mo", "1y", "5y"], value="1y")

# --- VERİ MOTORU (TEKLİ DETAY İÇİN) ---
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
                # Zamanları eşle
                df = df.join(usd['Close'].rename("kur"), how='left').ffill().bfill()
                # Gram hesaplama
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

# --- DETAY EKRANI ---
st.subheader(f"📊 {secilen_metin.split(' ')[0]} Analizi")

df = detay_veri_getir(secilen_kod, analiz_tipi, periyot)

if not df.empty:
    # Metrikler
    son = df['Close'].iloc[-1]
    onceki = df['Close'].iloc[-2]
    degisim_val = ((son - onceki) / onceki) * 100
    simge = "₺" if analiz_tipi == "TL (₺)" else "$"
    
    col1, col2, col3 = st.columns(3)
    
    # Renkli Metrik Kutusu
    renk = "normal"
    if degisim_val > 0: renk = "off" # Streamlit metric otomatik yeşil yapar
    else: renk = "inverse"
    
    col1.metric("Son Fiyat", f"{son:.2f} {simge}", f"%{degisim_val:.2f}")
    
    # En Yüksek / En Düşük (Seçilen Dönemde)
    en_yuksek = df['High'].max()
    en_dusuk = df['Low'].min()
    col2.metric("Dönem En Yüksek", f"{en_yuksek:.2f} {simge}")
    col3.metric("Dönem En Düşük", f"{en_dusuk:.2f} {simge}")
    
    # Grafik
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_width=[0.2, 0.7])
    
    # Mum Grafiği
    fig.add_trace(go.Candlestick(
        x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'],
        name="Fiyat"
    ), row=1, col=1)
    
    # Hacim Grafiği (Volume)
    fig.add_trace(go.Bar(x=df.index, y=df['Volume'], name="Hacim", marker_color='rgba(100, 100, 255, 0.5)'), row=2, col=1)
    
    fig.update_layout(template="plotly_dark", height=600, xaxis_rangeslider_visible=False, margin=dict(l=10, r=10, t=10, b=10))
    st.plotly_chart(fig, use_container_width=True)
    
else:
    st.error("Veri yüklenemedi. Piyasa kapalı veya bağlantı hatası olabilir.")
