import streamlit as st
import requests
from openai import OpenAI
import plotly.graph_objects as go
from datetime import datetime, timedelta

# --- SETUP ---
st.set_page_config(page_title="AI Price Predictor PRO", layout="wide")

# OpenAI Client initialisieren
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# --- KI FUNKTIONEN ---
def ask_ai_for_price_logic(product_name, news_snippets):
    """
    Fragt die KI nach einer Einschätzung basierend auf den News.
    """
    prompt = f"""
    Du bist ein Experte für den deutschen Einzelhandel. 
    Produkt: {product_name}
    Aktuelle News-Schlagzeilen: {news_snippets}
    
    Aufgabe:
    1. Schätze den aktuellen Durchschnittspreis in Deutschland (Euro).
    2. Bestimme einen 'Impact-Faktor' für die nächsten 3 Monate (z.B. 0.05 für +5%).
    3. Gib eine kurze Begründung.
    
    Antworte NUR im JSON Format:
    {{"preis": 1.29, "impact": 0.05, "grund": "Text"}}
    """
    
    response = client.chat.completions.create(
        model="gpt-3.5-turbo", # oder gpt-4o für bessere Ergebnisse
        messages=[{"role": "system", "content": "Du bist ein Preis-Analyst."},
                  {"role": "user", "content": prompt}]
    )
    return eval(response.choices[0].message.content)

# --- NEWS HOLEN ---
def fetch_news(product):
    url = f"https://newsapi.org/v2/everything?q={product}+preise+deutschland&apiKey={st.secrets['NEWS_API_KEY']}"
    articles = requests.get(url).json().get("articles", [])
    return [a['title'] for a in articles[:5]]

# --- UI ---
st.title("🤖 KI-Preis-Experte (Powered by OpenAI)")

produkt = st.text_input("Welches Produkt möchtest du prüfen?", "Bio-Eier")

if st.button("Analyse starten"):
    with st.spinner("KI liest Nachrichten und berechnet Preise..."):
        # 1. News sammeln
        headlines = fetch_news(produkt)
        news_text = " | ".join(headlines)
        
        # 2. KI Analyse
        analysis = ask_ai_for_price_logic(produkt, news_text)
        
        # --- DARSTELLUNG ---
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("KI-geschätzter Preis", f"{analysis['preis']:.2f} €")
            st.write(f"**Analyse:** {analysis['grund']}")
            
            if headlines:
                st.write("**Berücksichtigte News:**")
                for h in headlines:
                    st.caption(f"• {h}")

        with col2:
            # Prognose-Berechnung
            weeks = list(range(13))
            future_prices = [analysis['preis'] * (1 + (analysis['impact'] * (w/12))) for w in weeks]
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=weeks, y=future_prices, mode='lines+markers', name="Trend"))
            fig.update_layout(title="Prognose (Nächste 12 Wochen)", xaxis_title="Wochen", yaxis_title="Preis in €")
            st.plotly_chart(fig)
