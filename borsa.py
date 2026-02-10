import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np # Hesaplama için eklendi
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
st.set_page_config(page_title="Artek Finans Pro", layout="wide", page_icon="🦅")

# --- ZAMAN VE OTOMATİK YENİLEME ---
def simdi_tr():
    return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=3)))

tr_saat = simdi_tr()
saat = tr_saat.hour
dakika = tr_saat.minute

# Borsa 09:55 - 18:10 arası açık varsayalım (Geniş aralık)
borsa_acik_mi = False
if (9 <= saat < 18) or (saat == 18 and dakika <= 30):
    borsa_acik_mi = True
    if st_autorefresh:
        st_autorefresh(interval=60000, key="fiyat_yenileme")

# --- HAFIZA ---
if 'secilen_kod' not in st.session_state:
    st.session_state.secilen_kod = "GC=F"

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
    div[data-testid="stVerticalBlock"] > div[data-testid="stHorizontalBlock"] { align-items: center; border-bottom: 1px solid #374151; padding-bottom: 5px; margin-bottom: 5px; }
    .streamlit-expanderHeader { font-weight: bold; background-color: #1f2937; border-radius: 5px; }
    
    div[data-testid="stTextInput"] > div > div > input { background-color: #1f2937; color: white; border: 1px solid #4b5563; }
    
    /* Derinlik Çubuğu Stili */
    .depth-container { width: 100%; background-color: #374151; border-radius: 5px; height: 25px; display: flex; overflow: hidden; margin-top: 5px; }
    .depth-buy { background-color: #00c853; height: 100%; display: flex; align-items: center; justify-content: center; font-size: 12px; font-weight: bold; color: black; }
    .depth-sell { background-color: #d50000; height: 100%; display: flex; align-items: center; justify-content: center; font-size: 12px; font-weight: bold; color: white; }
</style>
""", unsafe_allow_html=True)

# --- BAŞLIK ---
col_logo, col_title = st.columns([1, 8])
with col_logo:
    st.image("https://cdn-icons-png.flaticon.com/512/3310/3310748.png", width=70)
with col_title:
    st.title("ARTEK FİNANS: BIST 100 PRO")
    durum_ikonu = "🟢" if borsa_acik_mi else "🔴"
    durum_mesaj = "Piyasa Açık" if borsa_acik_mi else "Piyasa Kapalı"
    st.caption(f"{durum_ikonu} {durum_mesaj} | Türkiye Saati: {tr_saat.strftime('%H:%M:%S')}")
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

def duygu_analizi(metin):
    metin = metin.lower()
    pozitif = ["rekor", "kar", "artış", "büyüme", "onay", "yükseliş", "temettü", "anlaşma", "dev", "imza", "tavan", "olumlu", "hedef", "güçlü", "al", "kazanç", "zirve"]
    negatif = ["düşüş", "zarar", "satış", "ceza", "kriz", "endişe", "iptal", "gerileme", "iflas", "taban", "olumsuz", "dava", "risk", "zayıf", "sat", "kayıp"]
    skor = 0
    for p in pozitif: 
        if p in metin: skor += 1
    for n in negatif: 
        if n in metin: skor -= 1
    return skor

# --- YAN MENÜ ---
st.sidebar.markdown("### ⚙️ Ayarlar")
analiz_tipi = st.sidebar.radio("Para Birimi", ["TL (₺)", "Dolar ($)"], horizontal=True)
periyot = st.sidebar.select_slider("Grafik Geçmişi", options=["1mo", "3mo", "1y", "5y"], value="1y")

st.sidebar.markdown("---")
st.sidebar.markdown("### 🦅 Piyasa Özeti")

arama_metni = st.sidebar.text_input("🔍 Hisse Ara", placeholder="Örn: THY, ASELS, KOZA...")

with st.spinner('Veriler güncelleniyor...'):
    degisimler = liste_ozeti_getir(HAM_LISTE)

def siralama_anahtari(kod): 
    return ISIM_SOZLUGU.get(kod, kod.replace(".IS", ""))
sirali_liste = sorted(HAM_LISTE, key=siralama_anahtari)

bulunan_sayisi = 0
for kod in sirali_liste:
    ad = ISIM_SOZLUGU.get(kod, kod.replace(".IS", ""))
    if arama_metni:
        if arama_metni.lower() not in ad.lower() and arama_metni.lower() not in kod.lower(): continue
    bulunan_sayisi += 1
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

if bulunan_sayisi == 0: st.sidebar.warning("Hisse bulunamadı.")

# --- SAĞ TARAF ---
secilen_ad = ISIM_SOZLUGU.get(st.session_state.secilen_kod, st.session_state.secilen_kod.replace(".IS", ""))

col_logo_header, col_text_header = st.columns([1, 15])
with col_logo_header:
    try:
        if "IS" in st.session_state.secilen_kod:
             logo_url = yf.Ticker(st.session_state.secilen_kod).info.get('logo_url')
             if logo_url: st.image(logo_url, width=60)
        elif "GC=F" in st.session_state.secilen_kod: st.image("https://cdn-icons-png.flaticon.com/512/10091/10091217.png", width=60)
        elif "SI=F" in st.session_state.secilen_kod: st.image("https://cdn-icons-png.flaticon.com/512/10091/10091334.png", width=60)
        elif "USD" in st.session_state.secilen_kod: st.image("https://cdn-icons-png.flaticon.com/512/2933/2933884.png", width=60)
    except: pass

with col_text_header:
    st.header(f"📊 {secilen_ad}")

tab_grafik, tab_haber, tab_bilgi = st.tabs(["📈 CANLI GRAFİK", "🗞️ HABER MERKEZİ (AI)", "📘 ŞİRKET KARTI"])

# --- 1. GRAFİK VE DERİNLİK SEKME ---
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
        
        # SMA Ekle
        df['SMA20'] = df['Close'].rolling(window=20).mean()

        c1, c2, c3 = st.columns(3)
        c1.metric("Anlık Değer", f"{son:.2f} {simge}", f"%{degisim_val:.2f}")
        c2.metric("En Yüksek", f"{df['High'].max():.2f} {simge}")
        c3.metric("En Düşük", f"{df['Low'].min():.2f} {simge}")
        
        # Grafik
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_width=[0.2, 0.7], vertical_spacing=0.05)
        fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name="Fiyat"), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df['SMA20'], line=dict(color='#fbbf24', width=1.5), name="SMA 20"), row=1, col=1)
        fig.add_trace(go.Bar(x=df.index, y=df['Volume'], name="Hacim", marker_color='rgba(100, 100, 255, 0.3)'), row=2, col=1)
        fig.update_layout(template="plotly_dark", height=500, xaxis_rangeslider_visible=False, margin=dict(l=10, r=10, t=30, b=10))
        st.plotly_chart(fig, use_container_width=True)

        # --- YENİ: DERİNLİK (VOLUME PROFILE) SİMÜLASYONU ---
        st.markdown("### 📊 Derinlik ve Alıcı/Satıcı Dengesi (Tahmini)")
        
        @st.cache_data(ttl=60)
        def hesapla_derinlik(sembol):
            try:
                # Günlük dakika verisini çek (Son 1 gün)
                df_intraday = yf.download(sembol, period="1d", interval="1m", progress=False)
                if df_intraday.empty: return 0, 0
                
                # Alış/Satış Ayrıştırma (Basit Heuristik: Kapanış > Açılış ise Alış, değilse Satış)
                buy_vol = df_intraday.loc[df_intraday['Close'] >= df_intraday['Open'], 'Volume'].sum()
                sell_vol = df_intraday.loc[df_intraday['Close'] < df_intraday['Open'], 'Volume'].sum()
                return buy_vol, sell_vol
            except: return 0, 0

        alis_lot, satis_lot = hesapla_derinlik(st.session_state.secilen_kod)
        
        if alis_lot + satis_lot > 0:
            toplam = alis_lot + satis_lot
            alis_yuzde = (alis_lot / toplam) * 100
            satis_yuzde = (satis_lot / toplam) * 100
            
            d1, d2 = st.columns(2)
            d1.metric("Alıcı Ağırlıklı Lot", f"{int(alis_lot):,}", f"%{alis_yuzde:.1f}")
            d2.metric("Satıcı Ağırlıklı Lot", f"{int(satis_lot):,}", f"-%{satis_yuzde:.1f}", delta_color="inverse")
            
            # Görsel Çubuk
            st.markdown(f"""
            <div class="depth-container">
                <div class="depth-buy" style="width: {alis_yuzde}%;">ALIŞ %{alis_yuzde:.0f}</div>
                <div class="depth-sell" style="width: {satis_yuzde}%;">SATIŞ %{satis_yuzde:.0f}</div>
            </div>
            <div style='text-align:center; font-size:11px; color:#9ca3af; margin-top:5px;'>
                *Not: Gerçek derinlik (Level 2) verisi ücretli olduğu için, bu veriler fiyat hareketlerine göre hesaplanan tahmini hacim dağılımıdır.
            </div>
            """, unsafe_allow_html=True)
        else:
            st.info("Bu seans için henüz yeterli derinlik/hacim verisi oluşmadı.")

    else: st.error("Veri alınamadı.")

with tab_haber:
    st.subheader(f"🧠 Yapay Zeka Haber Analizi: {secilen_ad}")
    with st.spinner("Haberler analiz ediliyor..."):
        try:
            googlenews = GoogleNews(lang='tr', region='TR')
            arama_terimi = f"{secilen_ad} hisse yorum" if "GRAM" not in secilen_ad else f"{secilen_ad} yorum"
            googlenews.search(arama_terimi)
            haberler = googlenews.results()
            if haberler:
                for haber in haberler[:10]:
                    baslik = haber['title']
                    tarih = haber['date']
                    link = haber['link']
                    ozet = haber.get('desc', 'Özet bilgi bulunamadı.')
                    puan = duygu_analizi(baslik)
                    if puan > 0: emoji = "🟢"; msj = "Pozitif"; tip = st.success
                    elif puan < 0: emoji = "🔴"; msj = "Negatif"; tip = st.error
                    else: emoji = "🔵"; msj = "Nötr"; tip = st.info
                    with st.expander(f"{emoji} {baslik}"):
                        tip(f"**AI Analizi:** {msj}")
                        st.write(f"📅 **Tarih:** {tarih}")
                        st.write(f"📝 **Özet:** {ozet}")
                        st.link_button("🔗 Habere Git", link)
            else: st.warning("Güncel haber bulunamadı.")
        except: st.error("Haber servisi hatası.")

with tab_bilgi:
    try:
        if "IS" in st.session_state.secilen_kod:
            ticker = yf.Ticker(st.session_state.secilen_kod)
            info = ticker.info
            st.write(f"**Sektör:** {info.get('sector', '-')}")
            st.write(f"**Endüstri:** {info.get('industry', '-')}")
            st.write(f"**Çalışan Sayısı:** {info.get('fullTimeEmployees', '-')}")
            st.markdown("### Şirket Özeti")
            st.write(info.get('longBusinessSummary', 'Açıklama bulunamadı.'))
        else: st.info("Emtia veya Döviz için şirket kartı bulunmaz.")
    except: st.write("Bilgi alınamadı.")
