import streamlit as st
import pandas as pd
import requests
import plotly.graph_objects as go
from datetime import datetime, timedelta

# --- SEITEN-LAYOUT ---
st.set_page_config(page_title="KI Preis-Orakel", layout="wide", page_icon="🛒")

# --- SECRETS LADEN ---
# Greift auf .streamlit/secrets.toml zu
try:
    NEWS_API_KEY = st.secrets["NEWS_API_KEY"]
except Exception:
    st.error("❌ NEWS_API_KEY nicht in den Secrets gefunden!")
    st.stop()

# --- NEWS FUNKTIONEN ---
@st.cache_data(ttl=3600)
def fetch_market_news(query):
    """Holt aktuelle News über die NewsAPI"""
    url = f"https://newsapi.org/v2/everything?q={query}&language=de&sortBy=publishedAt&apiKey={NEWS_API_KEY}"
    try:
        response = requests.get(url)
        data = response.json()
        return data.get("articles", [])[:10]
    except Exception as e:
        st.error(f"Fehler beim Abrufen der News: {e}")
        return []

def analyze_impact(articles):
    """Analysiert Schlagzeilen auf Preistreiber-Keywords"""
    keywords = {
        "steuer": 0.08, 
        "erhöhung": 0.05, 
        "teurer": 0.04, 
        "knapp": 0.03, 
        "dürre": 0.06, 
        "streik": 0.02,
        "energie": 0.04
    }
    score = 0
    found_headlines = []
    
    for art in articles:
        full_text = (art['title'] + (art['description'] or "")).lower()
        for kw, val in keywords.items():
            if kw in full_text:
                score += val
                found_headlines.append(art['title'])
                break # Nur ein Impact pro Artikel zählen
                
    return score, list(set(found_headlines))

# --- UI DESIGN ---
st.title("🛒 KI-gestützte Preisprognose")
st.markdown("Analysiert aktuelle Nachrichten auf **Preistreiber** für den deutschen Markt.")

# Sidebar für Benutzereingaben
st.sidebar.header("Produkteinstellungen")
produkt_name = st.sidebar.selectbox("Produkt wählen", ["Vollmilch", "Butter", "Brot (Weizen)", "Eier", "Kaffee"])
basis_preis = st.sidebar.number_input("Aktueller Preis in €", value=1.49, step=0.05)
zeitraum_wochen = st.sidebar.slider("Prognose-Zeitraum (Wochen)", 1, 12, 8)

# News abrufen basierend auf Produkt und Markt
suche = f"{produkt_name} PREIS ODER Lebensmittelpreise ODER Agrar"
news_articles = fetch_market_news(suche)
impact_score, wichtige_news = analyze_impact(news_articles)

# --- HAUPTBEREICH ---
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("Gefundene Marktsignale")
    if wichtige_news:
        for n in wichtige_news[:4]: # Top 4 News anzeigen
            st.warning(f"📰 {n}")
    else:
        st.info("Keine direkten Preistreiber in den News gefunden.")
    
    st.metric("Berechneter Risiko-Aufschlag", f"+{(impact_score * 100):.1f} %")

# --- BERECHNUNG DER PROGNOSE ---
dates = [datetime.now() + timedelta(weeks=i) for i in range(zeitraum_wochen + 1)]
prices = []

for i in range(len(dates)):
    # Grund-Inflation + News-Impact über die Zeit verteilt
    trend = 1 + (0.001 * i) # 0.1% pro Woche Basis
    news_shift = 1 + (impact_score * (i / zeitraum_wochen))
    prices.append(round(basis_preis * trend * news_shift, 2))

# --- GRAPH ---
with col2:
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=dates, y=prices, 
        mode='lines+markers',
        line=dict(color='#ff4b4b', width=4),
        name="Preisprognose"
    ))
    fig.update_layout(
        title=f"Preis-Trend für {produkt_name}",
        xaxis_title="Datum",
        yaxis_title="Preis in €",
        hovermode="x unified"
    )
    st.plotly_chart(fig, use_container_width=True)

# --- ZUSAMMENFASSUNG ---
st.divider()
final_price = prices[-1]
diff = ((final_price - basis_preis) / basis_preis) * 100

st.subheader("Ergebnis der Analyse")
st.write(f"Basierend auf den aktuellen Nachrichten wird der Preis für **{produkt_name}** "
         f"in {zeitraum_wochen} Wochen voraussichtlich bei ca. **{final_price:.2f} €** liegen "
         f"({diff:+.1f} % Veränderung).")
