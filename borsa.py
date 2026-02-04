import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from GoogleNews import GoogleNews
import datetime

# --- 1. SİTE AYARLARI ---
st.set_page_config(page_title="Raffık Finans", layout="wide", page_icon="🦅")

st.markdown("""
<style>
    .main { background-color: #0e1117; }
    h1 { color: #ffd700; font-family: 'Trebuchet MS', sans-serif; } /* Altın Sarısı Başlık */
    .stTabs [data-baseweb="tab-list"] { gap: 15px; }
    .stTabs [data-baseweb="tab"] { height: 45px; background-color: #1f2937; border-radius: 8px; color: white; border: 1px solid #374151; }
    .stTabs [aria-selected="true"] { background-color: #ffd700; color: black; font-weight: bold; border: none; }
    /* Metrik Kutuları */
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
    st.caption("🔴 Veriler anlık güncellenir (Gecikme: 15dk)")
st.markdown("---")

# --- YAN MENÜ ---
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/2910/2910312.png", width=120)
st.sidebar.markdown("### 🦅 Kontrol Paneli")

# Varlık Listesi
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
periyot = st.sidebar.select_slider("Grafik Geçmişi", options=["1mo", "3mo", "6mo", "1y", "2y", "5y"], value="1y")

# --- CANLI TUTMAK İÇİN BUTON ---
if st.sidebar.button("🔄 Verileri Şimdi Yenile"):
    st.cache_data.clear()

# --- YATIRIM SİMÜLASYONU ---
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

# --- MATEMATİK FONKSİYONLARI ---
def hesapla_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def hesapla_sma(series, period): return series.rolling(window=period).mean()
def hesapla_ema(series, period): return series.ewm(span=period, adjust=False).mean()

def haber_skoru(baslik):
    pozitif = ["rekor", "kar", "artış", "büyüme", "onay", "yükseliş", "temettü", "anlaşma", "dev", "imza"]
    negatif = ["düşüş", "zarar", "satış", "ceza", "kriz", "endişe", "iptal", "gerileme", "iflas"]
    score = 0
    baslik = baslik.lower()
    for k in pozitif: 
        if k in baslik: score += 1
    for k in negatif: 
        if k in baslik: score -= 1
    return score

# --- VERİ ÇEKME MOTORU (GÜNCELLENDİ: GRAM HESABI VE VERİ EŞLEME) ---
@st.cache_data(ttl=60) # 60 saniyede bir veriyi bayatlatıp yenisini çeker (Canlı kalmasını sağlar)
def veri_getir(sembol, tip, zaman):
    # Ana veriyi çek (Hisse veya ONS)
    df = yf.Ticker(sembol).history(period=zaman)
    
    # Veri boşsa hemen dön
    if df.empty:
        return df

    # --- ALTIN VE GÜMÜŞ ÖZEL HESAPLAMA (GRAM DÖNÜŞÜMÜ) ---
    if sembol in ["GC=F", "SI=F"]:
        if tip == "TL (₺)":
            # Dolar kurunu çek
            usd_try = yf.Ticker("USDTRY=X").history(period=zaman)
            
            # Zaman damgalarını eşitle (ÖNEMLİ: Grafiğin boş gelmemesi için)
            # Sadece 'Close' fiyatını alıp ana tabloya ekliyoruz
            df['USD_Rate'] = usd_try['Close']
            
            # Eksik günleri (tatiller vs) bir önceki günle doldur (Forward Fill)
            df['USD_Rate'] = df['USD_Rate'].ffill()
            
            # Formül: (ONS Fiyatı * Dolar Kuru) / 31.1035
            oz_to_gram = 31.1034768
            for col in ['Open', 'High', 'Low', 'Close']:
                df[col] = (df[col] * df['USD_Rate']) / oz_to_gram
                
        elif tip == "Dolar ($)":
            # Sadece ONS fiyatını 31.10'a bölüp Gram Dolar fiyatını bulabiliriz
            # Ya da ONS olarak bırakabiliriz. Kullanıcı "Gram" istediği için bölüyoruz.
            oz_to_gram = 31.1034768
            for col in ['Open', 'High', 'Low', 'Close']:
                df[col] = df[col] / oz_to_gram

    # --- HİSSELER İÇİN DOLAR BAZLI HESAP ---
    elif tip == "Dolar ($)" and "IS" in sembol:
        usd_try = yf.Ticker("USDTRY=X").history(period=zaman)
        df['USD_Rate'] = usd_try['Close']
        df['USD_Rate'] = df['USD_Rate'].ffill()
        for col in ['Open', 'High', 'Low', 'Close']:
            df[col] = df[col] / df['USD_Rate']
            
    return df

@st.cache_data(ttl=300) # Temel bilgiler 5 dakikada bir güncellense yeter
def temel_bilgi_getir(sembol):
    try:
        if "IS" in sembol:
            hisse_bilgi = yf.Ticker(sembol).info
            fk = hisse_bilgi.get('trailingPE', None)
            piyasa_deg = hisse_bilgi.get('marketCap', None)
            return fk, piyasa_deg
        return None, None
    except:
        return None, None

# --- ANA SAYFA ---
tab1, tab2, tab3 = st.tabs(["📈 CANLI GRAFİK", "📰 HABER MERKEZİ", "📘 BİLGİ BANKASI"])

with tab1:
    if secilen_kod:
        durum_metni, durum_kod = katilim_kontrol(secilen_kod)
        renk_css = "background-color: #065f46; color: #34d399;" if durum_kod == "ok" else ("background-color: #7f1d1d; color: #fca5a5;" if durum_kod == "red" else "background-color: #4b5563; color: #d1d5db;")
        st.markdown(f'<div style="{renk_css} padding: 10px; border-radius: 5px; font-weight: bold; text-align: center; margin-bottom: 10px;">{durum_metni}</div>', unsafe_allow_html=True)

        try:
            with st.spinner('Veriler Darphaneden Çekiliyor...'):
                df = veri_getir(secilen_kod, analiz_tipi, periyot)
            
            if not df.empty and len(df) > 1:
                # --- METRİKLER ---
                fk, mc = temel_bilgi_getir(secilen_kod)
                c1, c2, c3, c4 = st.columns(4)
                
                son_fiyat = df['Close'].iloc[-1]
                onceki_fiyat = df['Close'].iloc[-2]
                degisim = ((son_fiyat - onceki_fiyat) / onceki_fiyat) * 100
                simge = "$" if analiz_tipi == "Dolar ($)" else "₺"
                
                # Başlık Güncellemesi
                varlik_adi = isim_sozlugu.get(secilen_kod, secilen_kod)
                if secilen_kod in ["GC=F", "SI=F"]:
                    ek_bilgi = "(Gram Fiyatı)"
                else:
                    ek_bilgi = ""

                c1.metric(f"Son Fiyat {ek_bilgi}", f"{son_fiyat:.2f} {simge}", f"%{degisim:.2f}")
                
                if fk: c2.metric("F/K Oranı", f"{fk:.2f}")
                else: c2.metric("F/K Oranı", "-")
                    
                if mc: c3.metric("Piyasa Değeri", f"{(mc/1000000000):.1f} Mr {simge}")
                else: c3.metric("Piyasa Değeri", "-")
                
                # Simülasyon
                ilk_fiyat = df['Close'].iloc[0]
                simule_kar = (yatirim_miktari / ilk_fiyat) * son_fiyat
                fark_simule = simule_kar - yatirim_miktari
                c4.metric("Simülasyon Sonucu", f"{simule_kar:.0f} {simge}", f"{fark_simule:.0f} {simge}")
                st.divider()

                # --- GRAFİK ---
                df['SMA50'] = hesapla_sma(df['Close'], 50)
                df['EMA20'] = hesapla_ema(df['Close'], 20)
                df['RSI'] = hesapla_rsi(df['Close'], 14)

                fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.08, 
                                    subplot_titles=(f'{varlik_adi} Fiyat Analizi', 'RSI'), row_width=[0.25, 0.75])
                
                fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name='Fiyat', increasing_line_color='#00e676', decreasing_line_color='#ef4444'), row=1, col=1)
                fig.add_trace(go.Scatter(x=df.index, y=df['EMA20'], line=dict(color='#fbbf24', width=3), name='EMA 20'), row=1, col=1)
                fig.add_trace(go.Scatter(x=df.index, y=df['SMA50'], line=dict(color='#3b82f6', width=4), name='SMA 50'), row=1, col=1)
                fig.add_trace(go.Scatter(x=df.index, y=df['RSI'], line=dict(color='#d946ef', width=3), name='RSI'), row=2, col=1)
                
                fig.add_hline(y=70, line_dash="solid", line_color="#ef4444", row=2, col=1)
                fig.add_hline(y=30, line_dash="solid", line_color="#00e676", row=2, col=1)
                
                fig.update_layout(height=700, template="plotly_dark", xaxis_rangeslider_visible=False, plot_bgcolor="#0e1117", paper_bgcolor="#0e1117", font=dict(color="white"))
                st.plotly_chart(fig, use_container_width=True)
                
                csv = df.to_csv().encode('utf-8')
                st.download_button("📥 Verileri İndir", data=csv, file_name=f'{secilen_kod}_veriler.csv', mime='text/csv')

            else:
                st.warning("Veriler güncelleniyor veya piyasa kapalı olabilir. Lütfen 'Verileri Şimdi Yenile' butonuna basın.")
        except Exception as e:
            st.error(f"Bir hata oluştu: {e}")

with tab2:
    st.subheader(f"📰 {isim_sozlugu.get(secilen_kod, secilen_kod)} Gündemi")
    try:
        googlenews = GoogleNews(lang='tr', region='TR')
        if secilen_kod == "GC=F": term = "Altın yorum gram altın"
        elif secilen_kod == "SI=F": term = "Gümüş fiyatları yorum"
        else: term = f"{secilen_kod.replace('.IS', '')} hisse"
        
        googlenews.search(term)
        haberler = googlenews.results()
        if haberler:
            col_a, col_b = st.columns(2)
            for i, haber in enumerate(haberler[:10]):
                skor = haber_skoru(haber['title'])
                with (col_a if i % 2 == 0 else col_b):
                    if skor > 0: st.success(f"📈 {haber['title']}\n\n_{haber['date']}_")
                    elif skor < 0: st.error(f"📉 {haber['title']}\n\n_{haber['date']}_")
                    else: st.info(f"🗞️ {haber['title']}\n\n_{haber['date']}_")
        else:
            st.warning("Güncel haber akışı yok.")
    except:
        st.write("Haber servisine ulaşılamıyor.")

with tab3:
    st.info("**Gram Altın Hesabı:** Uluslararası ONS Altın fiyatı, o anki Dolar/TL kuruyla çarpılır ve 31.10'a (1 Ons) bölünerek hesaplanır.")
    st.info("**Canlı Veri:** Veriler Yahoo Finance üzerinden anlık çekilir. Piyasaların kapalı olduğu saatlerde son kapanış fiyatı görünür.")