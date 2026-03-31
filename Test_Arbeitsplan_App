import streamlit as st
import pandas as pd
from datetime import datetime

# --- SEITENKONFIGURATION ---
st.set_page_config(page_title="Studi-Schichtplaner", page_icon="📅", layout="wide")

# --- SIMULIERTE DATENBANK (Session State) ---
if "abteilungen" not in st.session_state:
    st.session_state.abteilungen = ["Kasse", "Lager", "Kundenservice"]

if "schichten" not in st.session_state:
    # Beispiel-Daten für den digitalisierten Plan
    st.session_state.schichten = pd.DataFrame([
        {"Datum": "2026-03-26", "Abteilung": "Kasse", "Mitarbeiter": "Alex", "Zeit": "08:00 - 16:00"},
        {"Datum": "2026-03-26", "Abteilung": "Lager", "Mitarbeiter": "Sam", "Zeit": "12:00 - 20:00"}
    ])

if "marktplatz" not in st.session_state:
    st.session_state.marktplatz = []

# --- NAVIGATION ---
st.title("🚀 Studi-Schicht-Hub")
auswahl = st.sidebar.radio("Navigation", ["📅 Digitaler Dienstplan", "🛒 Schicht-Marktplatz", "📸 Plan hochladen (OCR)"])

# --- 1. DIGITALER DIENSTPLAN ---
if auswahl == "📅 Digitaler Dienstplan":
    st.header("Aktueller Arbeitsplan")
    
    # Abteilungs-Filter (Sub-Threads)
    abt_filter = st.selectbox("Abteilung filtern:", ["Alle"] + st.session_state.abteilungen)
    
    daten = st.session_state.schichten
    if abt_filter != "Alle":
        daten = daten[daten["Abteilung"] == abt_filter]
        
    st.dataframe(daten, use_container_width=True)

# --- 2. MARKTPLATZ ---
elif auswahl == "🛒 Schicht-Marktplatz":
    st.header("Schicht-Marktplatz (Biete/Suche)")
    
    # Schicht anbieten
    with st.expander("➕ Schicht zum Tausch anbieten"):
        offene_schichten = st.session_state.schichten["Mitarbeiter"].unique()
        name = st.selectbox("Wer bist du?", offene_schichten)
        datum = st.date_input("Welcher Tag?")
        grund = st.text_input("Notiz (z.B. Klausur)")
        
        if st.button("Schicht freigeben"):
            st.session_state.marktplatz.append({
                "Von": name,
                "Datum": str(datum),
                "Grund": grund,
                "Status": "Offen"
            })
            st.success("Schicht auf dem Marktplatz gepostet!")

    # Marktplatz anzeigen
    st.subheader("Offene Angebote")
    if not st.session_state.marktplatz:
        st.info("Derzeit keine Schichten im Angebot. Alles super!")
    else:
        for idx, angebot in enumerate(st.session_state.marktplatz):
            if angebot["Status"] == "Offen":
                col1, col2 = st.columns([3, 1])
                col1.write(f"**{angebot['Von']}** gibt Schicht am **{angebot['Datum']}** ab. (Grund: {angebot['Grund']})")
                if col2.button("Übernehmen", key=f"take_{idx}"):
                    angebot["Status"] = "Übernommen"
                    st.success("Schicht erfolgreich übernommen!")
                    st.rerun()

# --- 3. OCR SCANNER (MANUELLE KORREKTUR) ---
elif auswahl == "📸 Plan hochladen (OCR)":
    st.header("Papier-Plan digitalisieren")
    
    uploaded_file = st.file_uploader("Foto des Aushangs hochladen...", type=["jpg", "png", "jpeg"])
    
    if uploaded_file is not None:
        st.image(uploaded_file, caption="Hochgeladenes Bild", width=300)
        st.info("🤖 Simuliere OCR-Auslesung... (Hier würde normalerweise die KI laufen)")
        
        # Simuliertes OCR-Ergebnis, das der Nutzer korrigieren kann
        ocr_daten = pd.DataFrame([
            {"Datum": "2026-03-27", "Abteilung": "Kasse", "Mitarbeiter": "FehlerhafterName123", "Zeit": "08:00 - 16:00"},
            {"Datum": "2026-03-27", "Abteilung": "Lager", "Mitarbeiter": "Lisa", "Zeit": "10:00 - 18:00"}
        ])
        
        st.warning("✏️ Bitte korrigiere eventuelle Lesefehler der KI in der Tabelle unten:")
        korrigierte_daten = st.data_editor(ocr_daten, use_container_width=True)
        
        if st.button("✅ Korrigierten Plan im System speichern"):
            st.session_state.schichten = pd.concat([st.session_state.schichten, korrigierte_daten], ignore_index=True)
            st.success("Plan erfolgreich integriert und für alle sichtbar!")
