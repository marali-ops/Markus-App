import streamlit as st
import requests
from openai import OpenAI
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json

# --- SETUP ---
st.set_page_config(page_title="AI Price Guru", layout="wide", page_icon="🤖")

# OpenAI Client (holt Key aus Streamlit Secrets)
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# --- KI FUNKTION: ANALYSE & EMPFEHLUNG ---
def get_ai_market_analysis(product, news_snippets):
    prompt = f"""
    Du bist ein Marktanalyst für deutsche Verbraucherpreise. 
    Produkt: {product}
    Aktuelle News: {news_snippets}
    
    Analysiere die Lage und gib folgendes im JSON-Format zurück:
    - aktueller_preis_schaetzung: (Ein realistischer Durchschnittspreis in Euro)
    - trend_faktor: (Prozentuale Änderung pro Monat, z.B. 0.05 für +5%)
    - grund: (Kurze Zusammenfassung der News-Lage)
    - empfehlung: (Eins von: 'Jetzt kaufen', 'Warten', 'Beobachten')
    - vorrat_nötig: (Ja/Nein)

    Nur das JSON ausgeben!
    """
    
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        response_format={ "type": "json_object" }
    )
    return json.loads(response.choices[0].message.content)

# --- NEWS FUNKTION ---
def get_headlines(product):
    api_key = st.secrets["NEWS_API_KEY"]
    url = f"https://newsapi.org/v2/everything?q={product}+preise+deutschland&apiKey={api_key}"
    try:
        data = requests.get(url).json()
        return [a['title'] for a in data.get("articles", [])[:5]]
    except:
        return []

# --- UI ---
st.title("🤖 AI Price Guru")
st.markdown("Kombiniert **Live-News** mit **OpenAI**, um deine Einkaufsvorteile zu berechnen.")

product_input = st.text_input("Welches Produkt möchtest du analysieren?", "Butter")

if st.button("Marktanalyse starten"):
    with st.spinner("KI analysiert Nachrichtenlage..."):
        # 1. Daten sammeln
        news = get_headlines(product_input)
        news_combined = " | ".join(news) if news else "Keine aktuellen News gefunden."
        
        # 2. KI befragen
        res = get_ai_market_analysis(product_input, news_combined)
        
        # --- ANZEIGE DER ERGEBNISSE ---
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("KI-Preis-Check", f"{res['aktueller_preis_schaetzung']:.2f} €")
            st.subheader("Strategie")
            color = "green" if res['empfehlung'] == "Jetzt kaufen" else "orange"
            st.markdown(f"### :{color}[{res['empfehlung']}]")

        with col2:
            st.info(f"**Grund:** {res['grund']}")
            if res['vorrat_nötig'] == "Ja":
                st.warning("⚠️ Vorratskauf empfohlen!")

        with col3:
            # Kleine Vorhersage-Kurve
            weeks = [0, 4, 8, 12]
            p_start = res['aktueller_preis_schaetzung']
            future_p = [p_start * (1 + (res['trend_faktor'] * (w/4))) for w in weeks]
            
            fig = go.Figure(go.Scatter(x=weeks, y=future_prices, line=dict(color='red')))
            fig.update_layout(title="Trend 3 Monate", height=200, margin=dict(l=0,r=0,t=30,b=0))
            st.plotly_chart(fig, use_container_width=True)

        if news:
            with st.expander("Gefundene Schlagzeilen"):
                for n in news:
                    st.write(f"• {n}")
