import streamlit as st
import requests
from openai import OpenAI
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json

# --- SETUP (Business-Look) ---
st.set_page_config(page_title="Portfolio-Optimierung: Konsum", layout="wide", page_icon="📈")

# OpenAI Client (holt Key aus Streamlit Secrets)
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# --- KI FUNKTION: ANALYSE MIT IRONISCHEM UNTERTON ---
def get_ai_market_analysis(product, news_snippets):
    prompt = f"""
    Du bist ein hochbezahlter Analyst für einen extrem erfolgreichen Geschäftsmann, 
    der Millionen verwaltet, aber bei Grundnahrungsmitteln wie Butter oder Eiern 
    jeden Cent zweimal umdreht. 

    Analysiere das Produkt: {product}
    Aktuelle News: {news_snippets}
    
    Analysiere die Lage und gib folgendes im JSON-Format zurück:
    - aktueller_preis_schaetzung: (Ein realistischer Durchschnittspreis in Euro)
    - trend_faktor: (Prozentuale Änderung pro Monat, z.B. 0.05 für +5%)
    - grund: (Eine professionell-ironische Zusammenfassung, die seinen Sparsinn schmeichelt)
    - empfehlung: (Eins von: 'Strategischer Kauf', 'Markt beobachten', 'Investment halten')
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
st.title("📈 Oaschbabier & ois wo ma a g'scheit Obacht gem muass")
st.markdown("### *Zentrale für Haushalts-Controlling & Sensible Konsumgüter*")
st.divider()

# Eingabefeld (Hier kann er das Produkt oder seinen Namen eingeben)
product_input = st.text_input("Produkt-Asset für Analyse eingeben:", "Butter")

if st.button("Analyse-Algorithmus starten"):
    
    # --- GEHEIMES GEBURTSTAGS-OSTER-EI ---
    # Ändere "markus" in seinen echten Namen um!
    if product_input.lower() in ["markus", "chef", "investor", "butterbaron"]:
        st.balloons()
        st.success("✨ **Sonderstatus aktiviert: Happy Birthday!**")
        
        col_a, col_b = st.columns([2, 1])
        with col_a:
            st.write(f"""
            ### Strategischer Sonderbericht zum Ehrentag
            Es wurde eine signifikante Abweichung in der heutigen Spar-Strategie festgestellt. 
            Die interne Revision ergibt: Eine Budget-Limitierung ist heute **unzulässig**. 
            
            **Analyse:** Das wichtigste Asset im Haushalt feiert heute Geburtstag. Der Marktwert ist unbezahlbar.
            **Empfehlung:** Streichfett-Optimierung sofort pausieren. Heute wird die Butter millimeterdick aufgetragen!
            """)
        with col_b:
            st.metric("Tages-Rendite", "100%", delta="Maximaler Spaßfaktor")
        
        st.info("P.S.: Wer beim Porsche nicht handelt, darf bei der Butter heute auch mal großzügig sein!")
        st.stop() # Stoppt die normale Analyse

    # --- NORMALE ANALYSE ---
    with st.spinner("Greife auf globale Marktdaten zu..."):
        news = get_headlines(product_input)
        news_combined = " | ".join(news) if news else "Keine kritischen Marktbewegungen gefunden."
        
        res = get_ai_market_analysis(product_input, news_combined)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Asset-Preis (Schätzung)", f"{res['aktueller_preis_schaetzung']:.2f} €")
            st.subheader("Handlungsstrategie")
            # Farbe je nach Empfehlung
            color = "green" if "Kauf" in res['empfehlung'] else "blue"
            st.markdown(f"### :{color}[{res['empfehlung']}]")

        with col2:
            st.info(f"**Marktanalyse:** {res['grund']}")
            if res['vorrat_nötig'] == "Ja":
                st.warning("⚠️ Strategischer Vorratsaufbau empfohlen!")

        with col3:
            # Trend-Graph
            weeks = [0, 4, 8, 12]
            p_start = res['aktueller_preis_schaetzung']
            future_p = [p_start * (1 + (res['trend_faktor'] * (w/4))) for w in weeks]
            
            fig = go.Figure(go.Scatter(x=weeks, y=future_p, line=dict(color='#1f77b4', width=3)))
            fig.update_layout(
                title="Prognostizierte Preispolitik (3M)", 
                height=220, 
                margin=dict(l=0,r=0,t=40,b=0),
                xaxis_title="Wochen",
                yaxis_title="€"
            )
            st.plotly_chart(fig, use_container_width=True)

        if news:
            with st.expander("Berücksichtigte Nachrichten-Quellen"):
                for n in news:
                    st.write(f"• {n}")
