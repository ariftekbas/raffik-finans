import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from GoogleNews import GoogleNews
import datetime

# --- 1. SİTE AYARLARI ---
st.set_page_config(page_title="Raffık Finans v2.1", layout="wide", page_icon="🦅")

st.markdown("""
<style>
    .main { background-color: #0e1117; }
    h1 { color: #ffd700; font-family: 'Trebuchet MS', sans-serif; }
    .stTabs [data-baseweb="tab-list"] { gap: 15px; }
    .stTabs [data-baseweb="tab"] { height: 45px; background-color: #1f2937; border-radius: 8px; color: white; border: 1px solid #374151; }
    .stTabs [aria-selected="true"] { background-color: #ffd700; color: black; font-weight: bold; border: none; }
    div[data-testid="stMetric"] { background-color: #1f2937; border: 1px solid #374151; padding: 10px; border-radius: 10px; }
    div[data-testid="stMetricLabel"] { color: #9ca3af; }
    div[data-testid="stMetricValue"] { color: #ffffff; }
</style>
""", unsafe_allow_html=True)

# --- BAŞLIK ---
col_logo, col_title = st.columns([1, 8])
with col_logo:
    st.image("https://cdn-icons-png.flaticon.com/512/3310/3310748.png", width=70)
with col_title:
    st.title("RAFFIK FİNANS: CANLI TAKİP")
    st.caption("🔴 Saatlik Veri Modu & Nan Savar Aktif")
st.markdown("---")

# --- YAN MENÜ ---
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/2910/2910312.png", width=120)
st.sidebar.markdown("### 🦅 Kontrol Paneli")

varlik_listesi = [
    "GC=F", "SI=F", 
    "THYAO.IS", "ASELS.IS", "BIMAS.IS", "EREGL.IS", "TUPRS.IS", 
    "AKBNK.IS", "GARAN.IS", "YKBNK.IS", "ISCTR.IS", "SAHOL.IS",
    "FROTO.IS", "TOASO.IS", "KCHOL.IS", "SASA.IS", "HEKTS.IS",
    "SISE.IS", "PETKM.IS", "PGSUS.IS", "ASTOR.IS", "KONTR.IS",
    "ENJSA.IS", "ALARK.IS", "ODAS.IS", "KOZAL.IS", "KRDMD.IS",
    "ARCLK.IS", "VESTL.IS", "EUPWR.IS", "CWENE.IS", "SMRTG.IS"
]

isim_sozlugu = {"GC=F": "🟡 GRAM ALTIN", "SI=F": "⚪ GRAM GÜMÜŞ"}

secilen_kod = st.sidebar.selectbox("Varlık Seçin", varlik_listesi, format_func=lambda x: isim_sozlugu.get(x, x))
analiz_tipi = st.sidebar.radio("Para Birimi", ["TL (₺)", "Dolar ($)"])

# YENİ: Zaman ve Aralık Ayarı
st.sidebar.markdown("---")
st.sidebar.write("⏱️ **Zaman Ayarları**")
periyot = st.sidebar.select_slider("Grafik Geçmişi", options=["1mo", "3mo", "6mo", "1y", "2y", "5y"], value="1mo")
# Saatlik veri seçeneği eklendi
aralik = st.sidebar.select_slider("Mum Aralığı (Hassasiyet)", options=["15m", "30m", "60m", "90m", "1d", "1wk"], value="60m")

if st.sidebar.button("🔄 Verileri Şimdi Yenile"):
    st.cache_data.clear()

st.sidebar.markdown("---")
st.sidebar.header("💰 Ne Olurdu?")
yatirim_miktari = st.sidebar.number_input("Yatırım Tutarı (TL)", value=10000, step=1000)

# --- KATILIM KONTROL ---
def katilim_kontrol(hisse):
    if hisse in ["GC=F", "SI=F"]: return "EMTİA (Uygun)", "ok"
    katilim_var = ["THYAO.IS", "BIMAS.IS", "ASELS.IS", "EREGL.IS", "TUPRS.IS", "FROTO.IS", "TOASO.IS", "SASA.IS", "ASTOR.IS", "KONTR.IS", "ENJSA.IS", "CWENE.IS", "EUPWR.IS", "ALARK.IS"]
    katilim_yok = ["AKBNK.IS", "GARAN.IS", "YKBNK.IS", "ISCTR.IS", "TSKB.IS", "VAKBN.IS", "HALKB.IS", "SAHOL.IS", "KCHOL.IS"]
    if hisse in katilim_var: return "✅ KATILIM ENDEKSİNE UYGUN", "ok"
    elif hisse in katilim_yok: return "⛔ KATILIM ENDEKSİNE UYGUN DEĞİL", "red"
    else: return "ℹ️ LİSTEDE YOK / KONTROL EDİLMELİ", "neutral"

# --- TEKNİK ANALİZ (Wilder's RSI) ---
def hesapla_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0))
    loss = (-delta.where(delta < 0, 0))
    avg_gain = gain.ewm(alpha=1/period, min_periods=period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/period, min_periods=period, adjust=False).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

def hesapla_sma(series, period): return series.rolling(window=period).mean()
def hesapla_ema(series, period): return series.ewm(span=period, adjust=False).mean()

def haber_skoru(baslik):
    pozitif = ["rekor", "kar", "artış", "büyüme", "onay", "yükseliş", "temettü", "anlaşma", "dev", "imza"]
    negatif = ["düşüş", "zarar", "satış", "ceza", "kriz", "endişe", "iptal", "gerileme", "iflas"]
    score = 0
    baslik = baslik.lower()
    for k in pozitif:
        if k in baslik:
            score += 1
    for k in negatif:
        if k in baslik:
            score -= 1
    return score

# --- VERİ ÇEKME MOTORU (SAATLİK HESAPLAMA DESTEKLİ) ---
@st.cache_data(ttl=60)
def veri_getir(sembol, tip, zaman, mum_araligi):
    # Ana veriyi çek (interval parametresi eklendi)
    try:
        df = yf.Ticker(sembol).history(period=zaman, interval=mum_araligi)
    except:
        return pd.DataFrame() # Hata olursa boş dön

    if df.empty: return df

    # 🛠️ Zaman dilimi temizliği (UTC sorununu çözer)
    df.index = df.index.tz_localize(None)

    # --- ALTIN VE GÜMÜŞ ÖZEL HESAPLAMA ---
    if sembol in ["GC=F", "SI=F"]:
        if tip == "TL (₺)":
            # Dolar kurunu da aynı aralıkta (örn: saatlik) çekiyoruz
            try:
                usd_try = yf.Ticker("USDTRY=X").history(period=zaman, interval=mum_araligi)
                usd_try.index = usd_try.index.tz_localize(None)
                
                # Verileri birleştir
                df = df.join(usd_try['Close'].rename("USD_Rate"), how='left')
                
                # Boşlukları doldur (Forward Fill + Backward Fill)
                df['USD_Rate'] = df['USD_Rate'].ffill().bfill()
                
                # Eğer Dolar verisi o aralıkta hiç yoksa son fiyatı al
                if df['USD_Rate'].isnull().all():
                     son_kur = yf.Ticker("USDTRY=X").fast_info['last_price']
                     df['USD_Rate'] = son_kur

                oz_to_gram = 31.1034768
                for col in ['Open', 'High', 'Low', 'Close']:
                    df[col] = (df[col] * df['USD_Rate']) / oz_to_gram
            except Exception as e:
                st.error(f"Dolar kuru alınırken hata: {e}")
                
        elif tip == "Dolar ($)":
            oz_to_gram = 31.1034768
            for col in ['Open', 'High', 'Low', 'Close']:
                df[col] = df[col] / oz_to_gram

    # --- HİSSELER İÇİN DOLAR BAZLI HESAP ---
    elif tip == "Dolar ($)" and "IS" in sembol:
        usd_try = yf.Ticker("USDTRY=X").history(period=zaman, interval=mum_araligi)
        usd_try.index = usd_try.index.tz_localize(None)
        df = df.join(usd_try['Close'].rename("USD_Rate"), how='left')
        df['USD_Rate'] = df['USD_Rate'].ffill().bfill()
        for col in ['Open', 'High', 'Low', 'Close']:
            df[col] = df[col] / df['USD_Rate']
            
    return df

@st.cache_data(ttl=300)
def temel_bilgi_getir(sembol):
    try:
        if "IS" in sembol:
            t = yf.Ticker(sembol)
            return t.info.get('trailingPE', None), t.fast_info.get('market_cap', None)
        return None, None
    except: return None, None

# --- ARAYÜZ ---
tab1, tab2, tab3 = st.tabs(["📈 CANLI GRAFİK", "📰 HABER MERKEZİ", "📘 BİLGİ BANKASI"])

with tab1:
    if secilen_kod:
        durum_metni, durum_kod = katilim_kontrol(secilen_kod)
        renk_css = "background-color: #065f46; color: #34d399;" if durum_kod == "ok" else ("background-color: #7f1d1d; color: #fca5a5;" if durum_kod == "red" else "background-color: #4b5563; color: #d1d5db;")
        st.markdown(f'<div style="{renk_css} padding: 10px; border-radius: 5px; font-weight: bold; text-align: center; margin-bottom: 10px;">{durum_metni}</div>', unsafe_allow_html=True)

        try:
            with st.spinner('Veriler İşleniyor...'):
                # Artık "aralik" değişkenini de gönderiyoruz
                df = veri_getir(secilen_kod, analiz_tipi, periyot, aralik)
            
            if not df.empty and len(df) > 1:
                fk, mc = temel_bilgi_getir(secilen_kod)
                c1, c2, c3, c4 = st.columns(4)
                
                son_fiyat = df['Close'].iloc[-1]
                onceki_fiyat = df['Close'].iloc[-2]
                degisim = ((son_fiyat - onceki_fiyat) / onceki_fiyat) * 100
                simge = "$" if analiz_tipi == "Dolar ($)" else "₺"
                ek_bilgi = "(Gram Fiyatı)" if secilen_kod in ["GC=F", "SI=F"] else ""

                c1.metric(f"Son Fiyat {ek_bilgi}", f"{son_fiyat:.2f} {simge}", f"%{degisim:.2f}")
                c2.metric("F/K Oranı", f"{fk:.2f}" if fk else "-")
                c3.metric("Piyasa Değeri", f"{(mc/1000000000):.1f} Mr {simge}" if mc else "-")
                
                ilk_fiyat = df['Close'].iloc[0]
                simule_kar = (yatirim_miktari / ilk_fiyat) * son_fiyat
                fark_simule = simule_kar - yatirim_miktari
                c4.metric("Simülasyon", f"{simule_kar:.0f} {simge}", f"{fark_simule:.0f} {simge}")
                st.divider()

                # --- GRAFİK ---
                df['SMA50'] = hesapla_sma(df['Close'], 50)
                df['EMA20'] = hesapla_ema(df['Close'], 20)
                df['RSI'] = hesapla_rsi(df['Close'], 14)

                fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.08, 
                                    subplot_titles=(f'{isim_sozlugu.get(secilen_kod, secilen_kod)} Fiyat Analizi', 'RSI (Wilder)'), row_width=[0.25, 0.75])
                
                fig.add_trace(go.Candlestick(
                    x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], 
                    name='Fiyat', increasing_line_color='#26a69a', decreasing_line_color='#ef5350'
                ), row=1, col=1)
                
                fig.add_trace(go.Scatter(x=df.index, y=df['EMA20'], line=dict(color='#fbbf24', width=2), name='EMA 20'), row=1, col=1)
                fig.add_trace(go.Scatter(x=df.index, y=df['SMA50'], line=dict(color='#3b82f6', width=2), name='SMA 50'), row=1, col=1)
                fig.add_trace(go.Scatter(x=df.index, y=df['RSI'], line=dict(color='#d946ef', width=2), name='RSI'), row=2, col=1)
                
                fig.add_hline(y=70, line_dash="solid", line_color="#ef4444", row=2, col=1)
                fig.add_hline(y=30, line_dash="solid", line_color="#00e676", row=2, col=1)
                
                fig.update_layout(height=700, template="plotly_dark", xaxis_rangeslider_visible=False, plot_bgcolor="#0e1117", paper_bgcolor="#0e1117", font=dict(color="white"))
                st.plotly_chart(fig, use_container_width=True)
                
                csv = df.to_csv().encode('utf-8')
                st.download_button("📥 İndir", data=csv, file_name=f'{secilen_kod}.csv', mime='text/csv')
            else:
                st.warning("Bu tarih aralığı için yeterli veri yok veya piyasa kapalı. Lütfen 'Mum Aralığı'nı veya 'Geçmişi' değiştirin.")
        except Exception as e:
            st.error(f"Hata: {e}")

with tab2:
    st.subheader("📰 Haber Akışı")
    try:
        googlenews = GoogleNews(lang='tr', region='TR')
        term = "Altın yorum" if secilen_kod == "GC=F" else ("Gümüş yorum" if secilen_kod == "SI=F" else f"{secilen_kod.replace('.IS', '')} hisse")
        googlenews.search(term)
        haberler = googlenews.results()
        if haberler:
            col_a, col_b = st.columns(2)
            for i, haber in enumerate(haberler[:8]):
                skor = haber_skoru(haber['title'])
                with (col_a if i % 2 == 0 else col_b):
                    if skor > 0: st.success(f"📈 {haber['title']}\n\n_{haber['date']}_")
                    elif skor < 0: st.error(f"📉 {haber['title']}\n\n_{haber['date']}_")
                    else: st.info(f"🗞️ {haber['title']}\n\n_{haber['date']}_")
        else: st.warning("Haber bulunamadı.")
    except: st.write("Haber servisi meşgul.")

with tab3:
    st.info("**Saatlik Veri Uyarısı:** Yahoo Finance kuralları gereği 15dk-60dk gibi veriler en fazla geriye dönük 60-730 gün için çekilebilir. Eğer grafik boş gelirse 'Grafik Geçmişi'ni '1mo' veya '3mo' yapın.")
    st.info("**Gram Hesaplaması:** Anlık ONS Altın fiyatı ile Anlık Dolar kuru çarpılarak hesaplanır. (Saatlik veride de bu çarpım her saat için ayrı ayrı yapılır).")

