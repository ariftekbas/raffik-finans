import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from GoogleNews import GoogleNews # Haber motorumuz
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

# --- CSS (Görsel Tasarım) ---
st.markdown("""
<style>
    .main { background-color: #0e1117; }
    h1 { color: #ffd700; font-family: 'Trebuchet MS', sans-serif; }
    div[data-testid="stMetric"] { background-color: #1f2937; border: 1px solid #374151; padding: 10px; border-radius: 10px; }
    
    /* Sekme (Tab) Tasarımı */
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] { background-color: #1f2937; border-radius: 5px; color: white; border: 1px solid #374151; }
    .stTabs [aria-selected="true"] { background-color: #ffd700; color: black; font-weight: bold; }

    /* Yan Menü Tasarımı */
    .badge { display: inline-flex; align-items: center; padding: 2px 8px; border-radius: 6px; font-weight: bold; font-size: 12px; margin-left: 5px; }
    .badge-up { background-color: #065f46; color: #34d399; }
    .badge-down { background-color: #7f1d1d; color: #fca5a5; }
    .badge-flat { background-color: #374151; color: #d1d5db; }
    .stock-name { font-weight: 600; font-size: 14px; color: #e5e7eb; }
    
    /* Buton Ayarı */
    div.stButton > button { padding: 0px 5px; min-height: 30px; height: 30px; line-height: 1; border: 1px solid #4b5563; }
    
    /* Yan menü hizalama */
    div[data-testid="stVerticalBlock"] > div[data-testid="stHorizontalBlock"] { align-items: center; border-bottom: 1px solid #374151; padding-bottom: 5px; margin-bottom: 5px; }
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

# --- LİSTE ---
HAM_LISTE = [
    "GC=F", "SI=F", "USDTRY=X",
    "THYAO.IS", "ASELS.IS", "BIMAS.IS", "EREGL.IS", "TUPRS.IS", 
    "AKBNK.IS", "GARAN.IS", "YKBNK.IS", "ISCTR.IS", "SAHOL.IS",
    "FROTO.IS", "TOASO.IS", "KCHOL.IS", "SASA.IS", "HEKTS.IS",
    "SISE.IS", "PETKM.IS", "PGSUS.IS", "ASTOR.IS", "KONTR.IS",
    "ENJSA.IS", "ALARK.IS", "ODAS.IS", "KOZAL.IS", "KRDMD.IS",
    "ARCLK.IS", "VESTL.IS", "EUPWR.IS", "CWENE.IS", "SMRTG.IS"
]

ISIM_SOZLUGU = { "GC=F": "GRAM ALTIN", "SI=F": "GRAM GÜMÜŞ", "USDTRY=X": "DOLAR/TL" }

# --- FONKSİYONLAR ---
@st.cache_data(ttl=60)
def liste_ozeti_getir(semboller):
    try:
        string_list = " ".join(semboller)
        data = yf.download(string_list, period="5d", group_by='ticker', progress=False)
        ozet_sozlugu = {}
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

# 🧠 YAPAY ZEKA SKORLAMA FONKSİYONU
def duygu_analizi(metin):
    metin = metin.lower()
    pozitif = ["rekor", "kar", "artış", "büyüme", "onay", "yükseliş", "temettü", "anlaşma", "dev", "imza", "tavan", "olumlu", "hedef", "güçlü", "al", "kazanç"]
    negatif = ["düşüş", "zarar", "satış", "ceza", "kriz", "endişe", "iptal", "gerileme", "iflas", "taban", "olumsuz", "dava", "risk", "zayıf", "sat"]
    
    skor = 0
    for p in pozitif: 
        if p in metin: skor += 1
    for n in negatif: 
        if n in metin: skor -= 1
    
    return skor

# --- YAN MENÜ: AYARLAR ---
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
    
    if yuzde > 0: badge = "badge-up"; icon = "↑"; yuzde_txt = f"%{yuzde:.2f}"
    elif yuzde < 0: badge = "badge-down"; icon = "↓"; yuzde_txt = f"%{abs(yuzde):.2f}"
    else: badge = "badge-flat"; icon = "-"; yuzde_txt = "%0.00"
    
    aktif_mi = "🟡" if st.session_state.secilen_kod == kod else ""
    
    col_txt, col_btn = st.sidebar.columns([0.8, 0.2])
    with col_txt:
        st.markdown(f"""<div style="display:flex; justify-content:space-between; align-items:center;"><span class="stock-name">{aktif_mi} {ad}</span><span class="badge {badge}">{icon} {yuzde_txt}</span></div>""", unsafe_allow_html=True)
    with col_btn:
        if st.button("➤", key=f"btn_{kod}"):
            st.session_state.secilen_kod = kod
            st.rerun()

# --- SAĞ TARAF: SEKMELİ YAPI ---
secilen_ad = ISIM_SOZLUGU.get(st.session_state.secilen_kod, st.session_state.secilen_kod.replace(".IS", ""))
st.header(f"📊 {secilen_ad}")

# Sekmeleri Oluştur
tab_grafik, tab_haber, tab_bilgi = st.tabs(["📈 CANLI GRAFİK", "🗞️ HABER MERKEZİ (AI)", "📘 ŞİRKET KARTI"])

# 1. SEKME: GRAFİK (Klasik Görünüm)
with tab_grafik:
    @st.cache_data(ttl=60)
    def detay_veri(sembol, tip, zaman):
        try:
            df = yf.Ticker(sembol).history(period=zaman)
            if df.empty: return pd.DataFrame()
            df.index = df.index.tz_localize(None)
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
    
    if not df.empty:
        son = df['Close'].iloc[-1]
        degisim_val = ((son - df['Close'].iloc[-2]) / df['Close'].iloc[-2]) * 100
        simge = "₺" if analiz_tipi == "TL (₺)" else "$"
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Son Fiyat", f"{son:.2f} {simge}", f"%{degisim_val:.2f}")
        c2.metric("En Yüksek", f"{df['High'].max():.2f} {simge}")
        c3.metric("En Düşük", f"{df['Low'].min():.2f} {simge}")
        
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_width=[0.2, 0.7], vertical_spacing=0.05)
        fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name="Fiyat"), row=1, col=1)
        fig.add_trace(go.Bar(x=df.index, y=df['Volume'], name="Hacim", marker_color='rgba(100, 100, 255, 0.5)'), row=2, col=1)
        fig.update_layout(template="plotly_dark", height=550, xaxis_rangeslider_visible=False)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.error("Veri alınamadı.")

# 2. SEKME: HABER MERKEZİ (İstediğin Renkli Haberler)
with tab_haber:
    st.subheader(f"🧠 Yapay Zeka Haber Analizi: {secilen_ad}")
    
    with st.spinner("İnternet taranıyor ve haberler analiz ediliyor..."):
        try:
            googlenews = GoogleNews(lang='tr', region='TR')
            # Arama kelimesini ayarla
            arama_terimi = f"{secilen_ad} hisse yorum" if "GRAM" not in secilen_ad else f"{secilen_ad} yorum"
            googlenews.search(arama_terimi)
            haberler = googlenews.results()
            
            if haberler:
                # Haberleri alt alta diz
                for haber in haberler[:10]: # En son 10 haber
                    baslik = haber['title']
                    tarih = haber['date']
                    link = haber['link']
                    
                    # 1. Duygu Analizi Yap
                    puan = duygu_analizi(baslik)
                    
                    # 2. Puana Göre Renk ve Kutu Seç
                    if puan > 0:
                        # POZİTİF -> YEŞİL
                        st.success(f"🟢 **{baslik}**\n\n_{tarih}_")
                    elif puan < 0:
                        # NEGATİF -> KIRMIZI
                        st.error(f"🔴 **{baslik}**\n\n_{tarih}_")
                    else:
                        # NÖTR -> MAVİ
                        st.info(f"🔵 **{baslik}**\n\n_{tarih}_")
            else:
                st.warning("Bu hisseyle ilgili güncel haber bulunamadı.")
                
        except Exception as e:
            st.error(f"Haber servisine bağlanırken hata oluştu: {e}")

# 3. SEKME: ŞİRKET KARTI (Özet Bilgi)
with tab_bilgi:
    try:
        if "IS" in st.session_state.secilen_kod:
            ticker = yf.Ticker(st.session_state.secilen_kod)
            info = ticker.info
            st.write(f"**Sektör:** {info.get('sector', 'Bilinmiyor')}")
            st.write(f"**Faaliyet Alanı:** {info.get('industry', 'Bilinmiyor')}")
            st.write(f"**Şirket Hakkında:**")
            st.write(info.get('longBusinessSummary', 'Açıklama bulunamadı.'))
        else:
            st.info("Bu bir Emtia veya Döviz çiftidir. Temel analiz verisi bulunmaz.")
    except:
        st.write("Bilgi alınamadı.")
