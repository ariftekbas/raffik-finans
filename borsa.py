import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from GoogleNews import GoogleNews
import datetime

# Otomatik yenileme
try:
    from streamlit_autorefresh import st_autorefresh
except ImportError:
    st_autorefresh = None

# --- 1. SİTE AYARLARI ---
st.set_page_config(page_title="Raffık Finans AI", layout="wide", page_icon="🦅")

if st_autorefresh:
    st_autorefresh(interval=60000, key="fiyat_yenileme")

# --- HAFIZA ---
if 'secilen_kod' not in st.session_state:
    st.session_state.secilen_kod = "GC=F"

# --- CSS STİLLERİ ---
st.markdown("""
<style>
    .main { background-color: #0e1117; }
    h1 { color: #ffd700; font-family: 'Trebuchet MS', sans-serif; }
    div[data-testid="stMetric"] { background-color: #1f2937; border: 1px solid #374151; padding: 10px; border-radius: 10px; }
    
    /* Yan Menü Düzeni */
    div[data-testid="stVerticalBlock"] > div[data-testid="stHorizontalBlock"] {
        align-items: center;
        border-bottom: 1px solid #374151;
        padding-bottom: 5px;
        margin-bottom: 5px;
    }
    
    .badge {
        display: inline-flex; align-items: center; padding: 2px 8px;
        border-radius: 6px; font-weight: bold; font-size: 12px; margin-left: 5px;
    }
    .badge-up { background-color: #065f46; color: #34d399; }
    .badge-down { background-color: #7f1d1d; color: #fca5a5; }
    .badge-flat { background-color: #374151; color: #d1d5db; }
    
    .stock-name { font-weight: 600; font-size: 14px; color: #e5e7eb; }
    
    div.stButton > button {
        padding: 0px 5px; min-height: 30px; height: 30px; line-height: 1; border: 1px solid #4b5563;
    }
</style>
""", unsafe_allow_html=True)

# --- BAŞLIK ---
col_logo, col_title = st.columns([1, 8])
with col_logo:
    st.image("https://cdn-icons-png.flaticon.com/512/3310/3310748.png", width=70)
with col_title:
    st.title("RAFFIK FİNANS: AI ANALİZ")
    st.caption(f"🔴 Yapay Zeka Haber Analizi Aktif | Son Güncelleme: {datetime.datetime.now().strftime('%H:%M:%S')}")
st.markdown("---")

# --- LİSTE TANIMLARI ---
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

# --- FONKSİYONLAR ---
@st.cache_data(ttl=60)
def liste_ozeti_getir(semboller):
    try:
        string_list = " ".join(semboller)
        data = yf.download(string_list, period="5d", group_by='ticker', progress=False)
        ozet_sozlugu = {}
        
        # Dolar değişimi
        try:
            usd_df = data["USDTRY=X"]['Close'].dropna()
            usd_change = ((usd_df.iloc[-1] - usd_df.iloc[-2]) / usd_df.iloc[-2]) if len(usd_df) > 1 else 0
        except: usd_change = 0

        for s in semboller:
            try:
                df = data[s]['Close'].dropna()
                if len(df) < 2: 
                    ozet_sozlugu[s] = 0.0
                    continue
                degisim = ((df.iloc[-1] - df.iloc[-2]) / df.iloc[-2])
                if s in ["GC=F", "SI=F"]: degisim = (1 + degisim) * (1 + usd_change) - 1
                ozet_sozlugu[s] = degisim
            except: ozet_sozlugu[s] = 0.0
        return ozet_sozlugu
    except: return {}

# YAPAY ZEKA ANALİZ MOTORU
def yapay_zeka_analiz(isim):
    try:
        googlenews = GoogleNews(lang='tr', region='TR')
        # Arama terimini optimize et
        term = f"{isim} hisse yorum" if "GRAM" not in isim else f"{isim} yorum"
        googlenews.search(term)
        haberler = googlenews.results()
        
        if not haberler: return 0, []

        pozitif_kelimeler = ["rekor", "kar", "artış", "büyüme", "onay", "yükseliş", "temettü", "anlaşma", "dev", "imza", "tavan", "olumlu", "hedef"]
        negatif_kelimeler = ["düşüş", "zarar", "satış", "ceza", "kriz", "endişe", "iptal", "gerileme", "iflas", "taban", "olumsuz", "dava"]
        
        skor = 0
        basliklar = []
        
        for haber in haberler[:5]: # Son 5 haberi analiz et
            baslik = haber['title'].lower()
            basliklar.append(haber['title'])
            for p in pozitif_kelimeler: 
                if p in baslik: skor += 1
            for n in negatif_kelimeler: 
                if n in baslik: skor -= 1
                
        return skor, basliklar
    except:
        return 0, []

# --- YAN MENÜ: AYARLAR (YUKARI TAŞINDI) ---
st.sidebar.markdown("### ⚙️ Ayarlar")
analiz_tipi = st.sidebar.radio("Para Birimi", ["TL (₺)", "Dolar ($)"], horizontal=True)
periyot = st.sidebar.select_slider("Grafik Geçmişi", options=["1mo", "3mo", "1y", "5y"], value="1y")

st.sidebar.markdown("---")
st.sidebar.markdown("### 🦅 Piyasa Özeti")

# --- YAN MENÜ: LİSTE ---
degisimler = liste_ozeti_getir(HAM_LISTE)
def siralama_anahtari(kod): return ISIM_SOZLUGU.get(kod, kod.replace(".IS", ""))
sirali_liste = sorted(HAM_LISTE, key=siralama_anahtari)

for kod in sirali_liste:
    ad = ISIM_SOZLUGU.get(kod, kod.replace(".IS", ""))
    yuzde = degisimler.get(kod, 0.0) * 100
    
    if yuzde > 0:
        badge = "badge-up"; icon = "↑"; yuzde_txt = f"%{yuzde:.2f}"
    elif yuzde < 0:
        badge = "badge-down"; icon = "↓"; yuzde_txt = f"%{abs(yuzde):.2f}"
    else:
        badge = "badge-flat"; icon = "-"; yuzde_txt = "%0.00"
    
    aktif_mi = "🟡" if st.session_state.secilen_kod == kod else ""
    
    col_txt, col_btn = st.sidebar.columns([0.8, 0.2])
    with col_txt:
        st.markdown(f"""
        <div style="display:flex; justify-content:space-between; align-items:center;">
            <span class="stock-name">{aktif_mi} {ad}</span>
            <span class="badge {badge}">{icon} {yuzde_txt}</span>
        </div>""", unsafe_allow_html=True)
    with col_btn:
        if st.button("➤", key=f"btn_{kod}"):
            st.session_state.secilen_kod = kod
            st.rerun()

# --- SAĞ TARAF: DETAY VE ANALİZ ---
secilen_ad = ISIM_SOZLUGU.get(st.session_state.secilen_kod, st.session_state.secilen_kod.replace(".IS", ""))

# Detay Verisi Çek
@st.cache_data(ttl=60)
def detay_veri(sembol, tip, zaman):
    try:
        df = yf.Ticker(sembol).history(period=zaman)
        if df.empty: return pd.DataFrame()
        df.index = df.index.tz_localize(None)
        
        # Kur dönüşümleri (Önceki kodun aynısı)
        if sembol in ["GC=F", "SI=F"]:
            usd = yf.Ticker("USDTRY=X").history(period=zaman)
            usd.index = usd.index.tz_localize(None)
            df = df.join(usd['Close'].rename("kur"), how='left').ffill().bfill()
            if tip == "TL (₺)": 
                for c in ['Open', 'High', 'Low', 'Close']: df[c] = (df[c] * df['kur']) / 31.1034768
            else:
                for c in ['Open', 'High', 'Low', 'Close']: df[c] = df[c] / 31.1034768
        elif tip == "Dolar ($)" and "IS" in sembol:
            usd = yf.Ticker("USDTRY=X").history(period=zaman)
            usd.index = usd.index.tz_localize(None)
            df = df.join(usd['Close'].rename("kur"), how='left').ffill().bfill()
            for c in ['Open', 'High', 'Low', 'Close']: df[c] = df[c] / df['kur']
        return df
    except: return pd.DataFrame()

df = detay_veri(st.session_state.secilen_kod, analiz_tipi, periyot)

# --- ANA SAYFA DÜZENİ ---
st.subheader(f"📊 {secilen_ad} Detayları")

# 1. YAPAY ZEKA ANALİZİ (EN ÜSTTE)
with st.spinner(f"🧠 Yapay Zeka {secilen_ad} için interneti tarıyor..."):
    ai_skor, haber_basliklari = yapay_zeka_analiz(secilen_ad)

# Skor Rengi Belirleme
if ai_skor > 0:
    st.success(f"**Yapay Zeka Görüşü: POZİTİF (Yeşil)** 🟢\n\nİnternetteki son haberler olumlu bir havaya işaret ediyor. Büyüme, kar veya anlaşma haberleri ağırlıkta.")
elif ai_skor < 0:
    st.error(f"**Yapay Zeka Görüşü: NEGATİF / RİSKLİ (Kırmızı)** 🔴\n\nPiyasada düşüş eğilimi, satış baskısı veya olumsuz gelişmeler konuşuluyor olabilir. Dikkatli olunmalı.")
else:
    st.info(f"**Yapay Zeka Görüşü: NÖTR (Mavi)** 🔵\n\nBelirgin bir olumlu ya da olumsuz haber akışı tespit edilemedi. Piyasa şu an kararsız veya yatay seyrediyor olabilir.")

# Haber Başlıklarını Genişletilebilir Alana Koy
with st.expander("🔍 Analiz Edilen Haber Başlıklarını Gör"):
    if haber_basliklari:
        for h in haber_basliklari:
            st.write(f"- {h}")
    else:
        st.write("Güncel haber bulunamadı.")

# 2. METRİKLER VE GRAFİK
if not df.empty:
    son = df['Close'].iloc[-1]
    degisim_val = ((son - df['Close'].iloc[-2]) / df['Close'].iloc[-2]) * 100
    simge = "₺" if analiz_tipi == "TL (₺)" else "$"
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Son Fiyat", f"{son:.2f} {simge}", f"%{degisim_val:.2f}")
    col2.metric("En Yüksek", f"{df['High'].max():.2f} {simge}")
    col3.metric("En Düşük", f"{df['Low'].min():.2f} {simge}")
    
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_width=[0.2, 0.7], vertical_spacing=0.05)
    fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name="Fiyat"), row=1, col=1)
    fig.add_trace(go.Bar(x=df.index, y=df['Volume'], name="Hacim", marker_color='rgba(100, 100, 255, 0.5)'), row=2, col=1)
    fig.update_layout(template="plotly_dark", height=550, xaxis_rangeslider_visible=False, margin=dict(l=10,r=10,t=10,b=10))
    st.plotly_chart(fig, use_container_width=True)
else:
    st.error("Veri alınamadı.")
