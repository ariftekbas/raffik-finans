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
GEMINI_API_KEY = "AIzaSyAohuPCw8DxngrgEavuiybzNCjRg3cS57Y"

# ==========================================
# ⚙️ SİTE YAPILANDIRMASI
# ==========================================
st.set_page_config(page_title="Artek Finans Pro", layout="wide", page_icon="🦅")

# Gemini Kurulumu ve Model Seçimi
AI_AKTIF = False
model = None

try:
    if GEMINI_API_KEY and "BURAYA" not in GEMINI_API_KEY:
        genai.configure(api_key=GEMINI_API_KEY)
        AI_AKTIF = True
except Exception as e:
    st.error(f"AI Başlatma Hatası: {e}")

try:
    from streamlit_autorefresh import st_autorefresh
except ImportError:
    st_autorefresh = None

# CSS Tasarımı
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
    
    /* Derinlik Çubuğu */
    .depth-container { width: 100%; background-color: #374151; border-radius: 5px; height: 25px; display: flex; overflow: hidden; margin-top: 5px; }
    .depth-buy { background-color: #00c853; height: 100%; display: flex; align-items: center; justify-content: center; font-size: 11px; font-weight: bold; color: black; }
    .depth-sell { background-color: #d50000; height: 100%; display: flex; align-items: center; justify-content: center; font-size: 11px; font-weight: bold; color: white; }
    
    div[data-testid="stTextInput"] > div > div > input { background-color: #1f2937; color: white; border: 1px solid #4b5563; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 🕒 ZAMAN VE OTOMATİK YENİLEME
# ==========================================
def simdi_tr():
    return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=3)))

tr_saat = simdi_tr()
borsa_acik_mi = False

# Hafta içi ve 09:00 - 18:30 arası açık kabul edelim
if tr_saat.weekday() < 5: 
    if (9 <= tr_saat.hour < 18) or (tr_saat.hour == 18 and tr_saat.minute <= 30):
        borsa_acik_mi = True
        if st_autorefresh:
            st_autorefresh(interval=60000, key="fiyat_yenileme")

# ==========================================
# 💾 HAFIZA YÖNETİMİ
# ==========================================
if 'secilen_kod' not in st.session_state:
    st.session_state.secilen_kod = "GC=F"
if 'favoriler' not in st.session_state:
    st.session_state.favoriler = []

# ==========================================
# 📊 VERİ LİSTELERİ
# ==========================================
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

ISIM_SOZLUGU = {
    "GC=F": "GRAM ALTIN", "SI=F": "GRAM GÜMÜŞ", "USDTRY=X": "DOLAR/TL",
    "THYAO.IS": "THY", "ASELS.IS": "ASELSAN", "BIMAS.IS": "BIM", "EREGL.IS": "EREGLI", "TUPRS.IS": "TUPRAS",
    "AKBNK.IS": "AKBANK", "GARAN.IS": "GARANTI", "YKBNK.IS": "YAPI KREDI", "ISCTR.IS": "IS BANKASI", "SAHOL.IS": "SABANCI HOL.",
    "FROTO.IS": "FORD OTO", "TOASO.IS": "TOFAS", "KCHOL.IS": "KOC HOLDING", "SASA.IS": "SASA POLY.", "HEKTS.IS": "HEKTAS",
    "SISE.IS": "SISECAM", "PETKM.IS": "PETKIM", "PGSUS.IS": "PEGASUS", "ASTOR.IS": "ASTOR ENERJI", "KONTR.IS": "KONTROLMATIK",
    "ENJSA.IS": "ENERJISA", "ALARK.IS": "ALARKO", "ODAS.IS": "ODAS ELEK.", "KOZAL.IS": "KOZA ALTIN", "KRDMD.IS": "KARDEMIR D",
    "ARCLK.IS": "ARCELIK", "VESTL.IS": "VESTEL", "EUPWR.IS": "EUROPOWER", "CWENE.IS": "CW ENERJI", "SMRTG.IS": "SMART GUNES",
    "MGROS.IS": "MIGROS", "TCELL.IS": "TURKCELL", "TTKOM.IS": "TURK TELEKOM", "EKGYO.IS": "EMLAK KONUT", "OYAKC.IS": "OYAK CIMENTO",
    "GUBRF.IS": "GUBRE FAB.", "DOHOL.IS": "DOGAN HOLDING", "SOKM.IS": "SOK MARKET", "ULKER.IS": "ULKER", "AEFES.IS": "ANADOLU EFES"
}

# ==========================================
# 🛠️ FONKSİYONLAR
# ==========================================

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

def google_rss_haberleri(arama_terimi):
    try:
        url = f"https://news.google.com/rss/search?q={arama_terimi}&hl=tr&gl=TR&ceid=TR:tr"
        response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=5)
        if response.status_code == 200:
            root = ET.fromstring(response.content)
            haberler = []
            for item in root.findall('.//item')[:5]: # Son 5 haber
                haberler.append({
                    'title': item.find('title').text, 
                    'link': item.find('link').text, 
                    'pubDate': item.find('pubDate').text
                })
            return haberler
        return []
    except: return []

# --- AKILLI AI FONKSİYONU (ÇOKLU MODEL DENEME) ---
def gemini_piyasa_ozeti(basliklar_listesi, hisse):
    if not AI_AKTIF:
        return "Yapay zeka anahtarı girilmediği için analiz yapılamıyor."
    
    basliklar_metni = "\n".join([f"- {b}" for b in basliklar_listesi])
    prompt = f"Borsa analistisin. '{hisse}' için haberleri TEK PARAGRAFTA özetle: {basliklar_metni}"
    
    # Sırayla Modelleri Dene
    modeller_listesi = ['gemini-1.5-flash', 'gemini-pro', 'gemini-1.0-pro']
    
    for m_adi in modeller_listesi:
        try:
            local_model = genai.GenerativeModel(m_adi)
            response = local_model.generate_content(prompt)
            return response.text.strip()
        except Exception:
            continue # Bu model çalışmadı, bir sonrakine geç
            
    return "⚠️ Üzgünüm, şu an hiçbir Yapay Zeka modeline bağlanılamadı. Lütfen API kotanızı kontrol edin."

def calculate_rsi(data, period=14):
    delta = data.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

# ==========================================
# 🖥️ ARAYÜZ
# ==========================================
col_logo, col_title = st.columns([1, 8])
with col_logo:
    st.image("https://cdn-icons-png.flaticon.com/512/3310/3310748.png", width=70)
with col_title:
    st.title("Artek Finans: Pro")
    durum_ikonu = "🟢" if borsa_acik_mi else "🔴"
    st.caption(f"{durum_ikonu} Piyasa Durumu | ⚠️ Veriler BIST kuralları gereği 15dk gecikmelidir.")
st.markdown("---")

# YAN MENÜ
st.sidebar.markdown("### ⚙️ Ayarlar")
analiz_tipi = st.sidebar.radio("Para Birimi", ["TL (₺)", "Dolar ($)"], horizontal=True)
periyot = st.sidebar.select_slider("Grafik Geçmişi", options=["1mo", "3mo", "1y", "5y"], value="1y")

if st.session_state.favoriler:
    st.sidebar.markdown("### ⭐ Favoriler")
    fav_sil = st.sidebar.selectbox("Favori Çıkar", ["Seç..."] + st.session_state.favoriler)
    if fav_sil != "Seç...":
        st.session_state.favoriler.remove(fav_sil)
        st.rerun()

st.sidebar.markdown("---")
arama_metni = st.sidebar.text_input("🔍 Hisse Ara / Ekle", placeholder="Örn: THY, ASELS...")

with st.spinner('Piyasa taranıyor...'):
    degisimler = liste_ozeti_getir(HAM_LISTE)

def siralama_anahtari(kod): 
    return ISIM_SOZLUGU.get(kod, kod.replace(".IS", ""))
sirali_liste = sorted(HAM_LISTE, key=siralama_anahtari)

st.sidebar.markdown("### 🦅 Piyasa Özeti")

for kod in sirali_liste:
    ad = ISIM_SOZLUGU.get(kod, kod.replace(".IS", ""))
    
    if arama_metni:
        if arama_metni.lower() not in ad.lower() and arama_metni.lower() not in kod.lower(): continue
    
    yuzde = degisimler.get(kod, 0.0) * 100
    if yuzde > 0: badge = "badge-up"; icon = "↑"; yuzde_txt = f"%{yuzde:.2f}"
    elif yuzde < 0: badge = "badge-down"; icon = "↓"; yuzde_txt = f"%{abs(yuzde):.2f}"
    else: badge = "badge-flat"; icon = "-"; yuzde_txt = "%0.00"
    
    aktif_mi = "🟡" if st.session_state.secilen_kod == kod else ""
    fav_ikon = "★" if kod in st.session_state.favoriler else "☆"

    c1, c2, c3 = st.sidebar.columns([0.15, 0.65, 0.2])
    if c1.button(fav_ikon, key=f"fav_{kod}"):
        if kod in st.session_state.favoriler: st.session_state.favoriler.remove(kod)
        else: st.session_state.favoriler.append(kod)
        st.rerun()
    with c2:
        st.markdown(f"""<div style="font-size:13px; font-weight:bold;">{aktif_mi} {ad} <span class="badge {badge}">{yuzde_txt}</span></div>""", unsafe_allow_html=True)
    if c3.button("➤", key=f"btn_{kod}"):
        st.session_state.secilen_kod = kod
        st.rerun()

# ANA EKRAN
secilen_ad = ISIM_SOZLUGU.get(st.session_state.secilen_kod, st.session_state.secilen_kod.replace(".IS", ""))

col_hd_1, col_hd_2 = st.columns([1, 15])
with col_hd_1:
    try:
        if "IS" in st.session_state.secilen_kod:
             l_url = yf.Ticker(st.session_state.secilen_kod).info.get('logo_url', '')
             if l_url: st.image(l_url, width=50)
        elif "GC=F" in st.session_state.secilen_kod: st.image("https://cdn-icons-png.flaticon.com/512/10091/10091217.png", width=50)
        elif "SI=F" in st.session_state.secilen_kod: st.image("https://cdn-icons-png.flaticon.com/512/10091/10091334.png", width=50)
        elif "USD" in st.session_state.secilen_kod: st.image("https://cdn-icons-png.flaticon.com/512/2933/2933884.png", width=50)
    except: pass
with col_hd_2:
    st.header(f"📊 {secilen_ad} Analiz Paneli")

tab_grafik, tab_haber, tab_bilgi = st.tabs(["📈 TEKNİK ANALİZ", "🗞️ PİYASA ÖZETİ (AI)", "📘 ŞİRKET KARTI"])

# --- TAB 1: TEKNİK ---
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
        df['SMA20'] = df['Close'].rolling(window=20).mean()
        df['SMA50'] = df['Close'].rolling(window=50).mean()
        df['RSI'] = calculate_rsi(df['Close'])

        son = df['Close'].iloc[-1]
        degisim_val = ((son - df['Close'].iloc[-2]) / df['Close'].iloc[-2]) * 100
        simge = "₺" if analiz_tipi == "TL (₺)" else "$"
        
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Fiyat", f"{son:.2f} {simge}", f"%{degisim_val:.2f}")
        m2.metric("RSI (14)", f"{df['RSI'].iloc[-1]:.1f}", help="30 Altı: Ucuz, 70 Üstü: Pahalı")
        m3.metric("SMA 20", f"{df['SMA20'].iloc[-1]:.2f}")
        m4.metric("Hacim", f"{df['Volume'].iloc[-1] / 1000000:.1f}M")

        fig = make_subplots(rows=3, cols=1, shared_xaxes=True, row_width=[0.2, 0.2, 0.6], vertical_spacing=0.03)
        fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name="Fiyat"), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df['SMA20'], line=dict(color='orange', width=1), name="SMA 20"), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df['SMA50'], line=dict(color='blue', width=1), name="SMA 50"), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df['RSI'], line=dict(color='purple', width=1.5), name="RSI"), row=2, col=1)
        fig.add_hline(y=70, line_dash="dot", row=2, col=1, line_color="red")
        fig.add_hline(y=30, line_dash="dot", row=2, col=1, line_color="green")
        fig.add_trace(go.Bar(x=df.index, y=df['Volume'], name="Hacim", marker_color='rgba(100, 100, 255, 0.3)'), row=3, col=1)
        fig.update_layout(template="plotly_dark", height=700, xaxis_rangeslider_visible=False, hovermode="x unified")
        st.plotly_chart(fig, use_container_width=True)

        # DÜRÜST İSİMLENDİRME: HACİM ANALİZİ
        st.markdown("### 📊 Gün İçi Hacim Analizi (Alıcı/Satıcı Dengesi)")
        @st.cache_data(ttl=60)
        def hesapla_hacim_analizi(sembol):
            try:
                df_int = yf.download(sembol, period="1d", interval="1m", progress=False)
                if df_int.empty: return 0, 0
                buy = df_int.loc[df_int['Close'] >= df_int['Open'], 'Volume'].sum()
                sell = df_int.loc[df_int['Close'] < df_int['Open'], 'Volume'].sum()
                return buy, sell
            except: return 0, 0

        alis, satis = hesapla_hacim_analizi(st.session_state.secilen_kod)
        if alis + satis > 0:
            top = alis + satis
            a_yuz = (alis / top) * 100
            s_yuz = (satis / top) * 100
            st.markdown(f"""
            <div class="depth-container">
                <div class="depth-buy" style="width: {a_yuz}%;">ALIŞ YÖNLÜ %{a_yuz:.0f}</div>
                <div class="depth-sell" style="width: {s_yuz}%;">SATIŞ YÖNLÜ %{s_yuz:.0f}</div>
            </div>""", unsafe_allow_html=True)
            st.caption("*Not: Bu veri gerçekleşen hacmin yönünü gösterir. Tahtadaki bekleyen emirler (Derinlik) değildir.*")
        else: st.info("Yeterli hacim verisi yok.")
    else: st.error("Veri alınamadı.")

# --- TAB 2: AI DESTEKLİ PİYASA ÖZETİ ---
with tab_haber:
    st.subheader(f"🧠 Yapay Zeka Baş Analisti: {secilen_ad}")
    
    haberler = google_rss_haberleri(f"{secilen_ad} hisse")
    
    if haberler:
        # 1. Başlıkları topla
        basliklar_listesi = [h['title'] for h in haberler]
        
        # 2. AI'ya toplu özet çıkart
        if AI_AKTIF:
            with st.spinner("Yapay zeka haberleri okuyup özetliyor..."):
                ozet_metni = gemini_piyasa_ozeti(basliklar_listesi, secilen_ad)
                
                # Eğer hata mesajı dönerse (içinde 'HATA' geçerse) kırmızı göster
                if "HATA" in ozet_metni:
                    st.error(ozet_metni)
                else:
                    st.info(f"📝 **AI PİYASA RAPORU:**\n\n{ozet_metni}")
        else:
            st.warning("⚠️ AI Anahtarı girilmediği veya hatalı olduğu için otomatik özet yapılamıyor.")

        # 3. Haber Kaynaklarını Listele
        st.markdown("---")
        st.markdown("**🔍 Kaynak Haberler:**")
        for h in haberler:
            st.write(f"🔗 [{h['title']}]({h['link']}) - *{h['pubDate']}*")
    else:
        st.info("Güncel haber bulunamadı.")

with tab_bilgi:
    try:
        if "IS" in st.session_state.secilen_kod:
            tik = yf.Ticker(st.session_state.secilen_kod)
            st.write(f"**Sektör:** {tik.info.get('sector', '-')}")
            st.write(tik.info.get('longBusinessSummary', ''))
        else: st.info("Şirket verisi yok.")
    except: st.write("Bilgi alınamadı.")
