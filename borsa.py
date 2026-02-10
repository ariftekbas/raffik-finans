import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import datetime
import requests
import xml.etree.ElementTree as ET

# Otomatik yenileme
try:
    from streamlit_autorefresh import st_autorefresh
except ImportError:
    st_autorefresh = None

# --- 1. SİTE AYARLARI ---
st.set_page_config(page_title="Artek Finans ", layout="wide", page_icon="🦅")

# --- ZAMAN VE OTOMATİK YENİLEME ---
def simdi_tr():
    return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=3)))
tr_saat = simdi_tr()

# Borsa Saati Kontrolü
borsa_acik_mi = False
if (9 <= tr_saat.hour < 18) or (tr_saat.hour == 18 and tr_saat.minute <= 30):
    borsa_acik_mi = True
    if st_autorefresh:
        st_autorefresh(interval=60000, key="fiyat_yenileme")

# --- HAFIZA BAŞLATMA ---
if 'secilen_kod' not in st.session_state:
    st.session_state.secilen_kod = "GC=F"
if 'favoriler' not in st.session_state:
    st.session_state.favoriler = [] # Favori listesi hafızası

# --- CSS ---
st.markdown("""
<style>
    .main { background-color: #0e1117; }
    h1 { color: #ffd700; font-family: 'Trebuchet MS', sans-serif; }
    div[data-testid="stMetric"] { background-color: #1f2937; border: 1px solid #374151; padding: 10px; border-radius: 10px; }
    .badge { display: inline-flex; align-items: center; padding: 2px 8px; border-radius: 6px; font-weight: bold; font-size: 12px; margin-left: 5px; }
    .badge-up { background-color: #065f46; color: #34d399; }
    .badge-down { background-color: #7f1d1d; color: #fca5a5; }
    .badge-flat { background-color: #374151; color: #d1d5db; }
    .stock-name { font-weight: 600; font-size: 14px; color: #e5e7eb; }
    div.stButton > button { padding: 0px 5px; min-height: 30px; height: 30px; line-height: 1; border: 1px solid #4b5563; }
    div[data-testid="stTextInput"] > div > div > input { background-color: #1f2937; color: white; border: 1px solid #4b5563; }
</style>
""", unsafe_allow_html=True)

# --- BAŞLIK ---
col_logo, col_title = st.columns([1, 8])
with col_logo:
    st.image("https://cdn-icons-png.flaticon.com/512/3310/3310748.png", width=70)
with col_title:
    st.title("Artek Finans" +"
    /n Bist 100")
    durum_ikonu = "🟢" if borsa_acik_mi else "🔴"
    # DÜRÜSTLÜK GÜNCELLEMESİ: Gecikme uyarısı eklendi
    st.caption(f"{durum_ikonu} Piyasa Durumu | ⚠️ Veriler BIST kuralları gereği 15dk gecikmelidir.")
st.markdown("---")

# --- LİSTE ---
HAM_LISTE = [
    "GC=F", "SI=F", "USDTRY=X",
    "AEFES.IS", "AGHOL.IS", "AHGAZ.IS", "AKBNK.IS", "AKCNS.IS", "AKFGY.IS", "AKFYE.IS", "AKSA.IS", "AKSEN.IS", "ALARK.IS", 
    "ALBRK.IS", "ALFAS.IS", "ARCLK.IS", "ASELS.IS", "ASTOR.IS", "ASUZU.IS", "AYDEM.IS", "BAGFS.IS", "BERA.IS", "BIMAS.IS", 
    "BIOEN.IS", "BRSAN.IS", "BRYAT.IS", "BUCIM.IS", "CANTE.IS", "CCOLA.IS", "CEMTS.IS", "CIMSA.IS", "CWENE.IS", "DOAS.IS", 
    "DOHOL.IS", "ECILC.IS", "ECZYT.IS", "EGEEN.IS", "EKGYO.IS", "ENJSA.IS", "ENKAI.IS", "EREGL.IS", "EUPWR.IS", "EUREN.IS", 
    "FROTO.IS", "GARAN.IS", "GENIL.IS", "GESAN.IS", "GLYHO.IS", "GSDHO.IS", "GUBRF.IS", "GWIND.IS", "HALKB.IS", "HEKTS.IS", 
    "IPEKE.IS", "ISCTR.IS", "ISDMR.IS", "ISFIN.IS", "ISGYO.IS", "ISMEN.IS", "IZMDC.IS", "KARSN.IS", "KCAER.IS", "KCHOL.IS", 
    "KONTR.IS", "KONYA.IS", "KORDS.IS", "KOZAA.IS", "KOZAL.IS", "KRDMD.IS", "KZBGY.IS", "MAVI.IS", "MGROS.IS", "MIATK.IS", 
    "ODAS.IS", "OTKAR.IS", "OYAKC.IS", "PENTA.IS", "PETKM.IS", "PGSUS.IS", "PSGYO.IS", "QUAGR.IS", "SAHOL.IS", "SASA.IS", 
    "SISE.IS", "SKBNK.IS", "SMRTG.IS", "SNGYO.IS", "SOKM.IS", "TAVHL.IS", "TCELL.IS", "THYAO.IS", "TKFEN.IS", "TOASO.IS", 
    "TSKB.IS", "TTKOM.IS", "TTRAK.IS", "TUKAS.IS", "TUPRS.IS", "TURSG.IS", "ULKER.IS", "VAKBN.IS", "VESBE.IS", "VESTL.IS", 
    "YEOTK.IS", "YKBNK.IS", "YYLGD.IS", "ZOREN.IS"
]

ISIM_SOZLUGU = { "GC=F": "GRAM ALTIN", "SI=F": "GRAM GÜMÜŞ", "USDTRY=X": "DOLAR/TL" } # (Kısaltıldı, eski kodundaki liste aynı kalacak)

# --- FONKSİYONLAR ---
@st.cache_data(ttl=60)
def liste_ozeti_getir(semboller):
    try:
        string_list = " ".join(semboller)
        data = yf.download(string_list, period="5d", group_by='ticker', progress=False)
        ozet_sozlugu = {}
        # Dolar değişimi (Gram hesapları için)
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

def google_rss_haberleri(arama_terimi):
    try:
        url = f"https://news.google.com/rss/search?q={arama_terimi}&hl=tr&gl=TR&ceid=TR:tr"
        response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
        if response.status_code == 200:
            root = ET.fromstring(response.content)
            haberler = []
            for item in root.findall('.//item')[:10]:
                haberler.append({'title': item.find('title').text, 'link': item.find('link').text, 'pubDate': item.find('pubDate').text})
            return haberler
        return []
    except: return []

# --- TEKNİK ANALİZ FONKSİYONLARI (YENİ) ---
def calculate_rsi(data, period=14):
    delta = data.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

# --- YAN MENÜ ---
st.sidebar.markdown("### ⚙️ Ayarlar")
analiz_tipi = st.sidebar.radio("Para Birimi", ["TL (₺)", "Dolar ($)"], horizontal=True)
periyot = st.sidebar.select_slider("Grafik Geçmişi", options=["1mo", "3mo", "1y", "5y"], value="1y")

# --- YENİ: FAVORİLER BÖLÜMÜ ---
if st.session_state.favoriler:
    st.sidebar.markdown("### ⭐ Favoriler")
    fav_sil = st.sidebar.selectbox("Favori Çıkar", ["Seç..."] + st.session_state.favoriler)
    if fav_sil != "Seç...":
        st.session_state.favoriler.remove(fav_sil)
        st.rerun()

st.sidebar.markdown("---")
arama_metni = st.sidebar.text_input("🔍 Hisse Ara / Ekle", placeholder="Örn: THY, ASELS...")

with st.spinner('Veriler güncelleniyor...'):
    degisimler = liste_ozeti_getir(HAM_LISTE)

def siralama_anahtari(kod): 
    return ISIM_SOZLUGU.get(kod, kod.replace(".IS", ""))
sirali_liste = sorted(HAM_LISTE, key=siralama_anahtari)

# LİSTELEME
st.sidebar.markdown("### 🦅 Piyasa Özeti")

for kod in sirali_liste:
    ad = ISIM_SOZLUGU.get(kod, kod.replace(".IS", ""))
    
    # Filtreleme: Hem arama kutusu hem favori filtresi
    if arama_metni:
        if arama_metni.lower() not in ad.lower() and arama_metni.lower() not in kod.lower(): continue
    
    yuzde = degisimler.get(kod, 0.0) * 100
    if yuzde > 0: badge = "badge-up"; icon = "↑"; yuzde_txt = f"%{yuzde:.2f}"
    elif yuzde < 0: badge = "badge-down"; icon = "↓"; yuzde_txt = f"%{abs(yuzde):.2f}"
    else: badge = "badge-flat"; icon = "-"; yuzde_txt = "%0.00"
    
    aktif_mi = "🟡" if st.session_state.secilen_kod == kod else ""
    fav_ikon = "★" if kod in st.session_state.favoriler else "☆"

    c1, c2, c3 = st.sidebar.columns([0.15, 0.65, 0.2])
    
    # Favori Ekleme Butonu
    if c1.button(fav_ikon, key=f"fav_{kod}"):
        if kod in st.session_state.favoriler: st.session_state.favoriler.remove(kod)
        else: st.session_state.favoriler.append(kod)
        st.rerun()
        
    with c2:
        st.markdown(f"""<div style="font-size:13px; font-weight:bold;">{aktif_mi} {ad} <span class="badge {badge}">{yuzde_txt}</span></div>""", unsafe_allow_html=True)
    
    if c3.button("➤", key=f"btn_{kod}"):
        st.session_state.secilen_kod = kod
        st.rerun()

# --- SAĞ TARAF ---
secilen_ad = ISIM_SOZLUGU.get(st.session_state.secilen_kod, st.session_state.secilen_kod.replace(".IS", ""))
st.header(f"📊 {secilen_ad}")

tab_grafik, tab_haber, tab_bilgi = st.tabs(["📈 TEKNİK ANALİZ", "🗞️ HABERLER", "📘 BİLGİ"])

with tab_grafik:
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
    
    if not df.empty:
        son = df['Close'].iloc[-1]
        degisim_val = ((son - df['Close'].iloc[-2]) / df['Close'].iloc[-2]) * 100
        simge = "₺" if analiz_tipi == "TL (₺)" else "$"
        
        # --- TEKNİK İNDİKATÖRLER ---
        df['SMA20'] = df['Close'].rolling(window=20).mean()
        df['SMA50'] = df['Close'].rolling(window=50).mean()
        df['RSI'] = calculate_rsi(df['Close'])

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Fiyat", f"{son:.2f} {simge}", f"%{degisim_val:.2f}")
        c2.metric("RSI (14)", f"{df['RSI'].iloc[-1]:.2f}", help="70 üstü aşırı alım (satış riski), 30 altı aşırı satım (alım fırsatı)")
        c3.metric("SMA 20", f"{df['SMA20'].iloc[-1]:.2f}", help="Kısa vadeli trend ortalaması")
        c4.metric("SMA 50", f"{df['SMA50'].iloc[-1]:.2f}", help="Orta vadeli trend ortalaması")
        
        # Grafik: Fiyat + RSI
        fig = make_subplots(rows=3, cols=1, shared_xaxes=True, row_width=[0.2, 0.2, 0.6], vertical_spacing=0.05)
        
        # 1. Fiyat
        fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name="Fiyat"), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df['SMA20'], line=dict(color='orange', width=1), name="SMA 20"), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df['SMA50'], line=dict(color='blue', width=1), name="SMA 50"), row=1, col=1)

        # 2. RSI
        fig.add_trace(go.Scatter(x=df.index, y=df['RSI'], line=dict(color='purple', width=1.5), name="RSI"), row=2, col=1)
        fig.add_hline(y=70, line_dash="dot", row=2, col=1, line_color="red")
        fig.add_hline(y=30, line_dash="dot", row=2, col=1, line_color="green")

        # 3. Hacim
        fig.add_trace(go.Bar(x=df.index, y=df['Volume'], name="Hacim", marker_color='rgba(100, 100, 255, 0.3)'), row=3, col=1)
        
        fig.update_layout(template="plotly_dark", height=700, xaxis_rangeslider_visible=False)
        st.plotly_chart(fig, use_container_width=True)
    else: st.error("Veri alınamadı.")

# (Haberler ve Bilgi Sekmeleri önceki kodla aynı kalabilir, yer tutması için basitleştirildi)
with tab_haber:
    st.write("Haber akışı güncelleniyor...")
    # RSS Haber kodunu buraya entegre edebilirsin (yukarıdaki fonksiyondan)
    haberler = google_rss_haberleri(f"{secilen_ad} hisse")
    for h in haberler:
        st.info(f"📰 [{h['title']}]({h['link']}) \n *{h['pubDate']}*")

with tab_bilgi:
     st.write("Şirket kartı bilgileri...")


