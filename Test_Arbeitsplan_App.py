import streamlit as st
import pandas as pd
import numpy as np
import easyocr
from PIL import Image
from datetime import datetime

# --- SEITENKONFIGURATION ---
st.set_page_config(page_title="Studi-Schicht-Hub", page_icon="📅", layout="wide")

# --- INITIALISIERUNG DER DATENBANK (Session State) ---
# Das sorgt dafür, dass Daten während der Sitzung erhalten bleiben
if "abteilungen" not in st.session_state:
    st.session_state.abteilungen = ["Kasse", "Lager", "Kundenservice", "Gastronomie"]

if "schichten" not in st.session_state:
    # Start-Daten
    st.session_state.schichten = pd.DataFrame([
        {"Datum": "2026-03-30", "Abteilung": "Kasse", "Mitarbeiter": "Alex", "Zeit": "08:00 - 16:00"},
        {"Datum": "2026-03-30", "Abteilung": "Lager", "Mitarbeiter": "Sam", "Zeit": "12:00 - 20:00"}
    ])

if "marktplatz" not in st.session_state:
    st.session_state.marktplatz = []

# --- FUNKTION: OCR AUSFÜHRUNG ---
@st.cache_resource # Verhindert, dass das KI-Modell bei jedem Klick neu geladen wird
def get_ocr_reader():
    return easyocr.Reader(['de'])

# --- NAVIGATION ---
st.sidebar.title("📌 Menü")
auswahl = st.sidebar.radio("Gehe zu:", ["📅 Digitaler Dienstplan", "🛒 Schicht-Marktplatz", "📸 Plan hochladen (OCR)"])

# --- 1. DIGITALER DIENSTPLAN ---
if auswahl == "📅 Digitaler Dienstplan":
    st.header("📅 Aktueller Arbeitsplan")
    
    col1, col2 = st.columns([2, 1])
    with col1:
        abt_filter = st.selectbox("Abteilung filtern:", ["Alle"] + st.session_state.abteilungen)
    
    daten = st.session_state.schichten
    if abt_filter != "Alle":
        daten = daten[daten["Abteilung"] == abt_filter]
        
    st.dataframe(daten, use_container_width=True, hide_index=True)

# --- 2. MARKTPLATZ ---
elif auswahl == "🛒 Schicht-Marktplatz":
    st.header("🛒 Schicht-Marktplatz")
    st.write("Biete hier Schichten an, die du nicht wahrnehmen kannst.")
    
    with st.expander("➕ Neue Schicht zum Tausch anbieten"):
        name = st.text_input("Dein Name")
        datum = st.date_input("Datum der Schicht", value=datetime.now())
        zeit = st.text_input("Zeitraum (z.B. 08:00 - 16:00)")
        grund = st.text_area("Grund / Info für Kollegen")
        
        if st.button("Auf Marktplatz posten"):
            if name and zeit:
                st.session_state.marktplatz.append({
                    "Von": name,
                    "Datum": str(datum),
                    "Zeit": zeit,
                    "Grund": grund,
                    "Status": "Offen"
                })
                st.success("Erfolgreich inseriert!")
            else:
                st.error("Bitte Name und Zeit angeben.")

    st.subheader("Offene Angebote")
    if not st.session_state.marktplatz:
        st.info("Keine offenen Schicht-Angebote vorhanden.")
    else:
        for idx, angebot in enumerate(st.session_state.marktplatz):
            if angebot["Status"] == "Offen":
                with st.container(border=True):
                    c1, c2 = st.columns([3, 1])
                    c1.write(f"👤 **{angebot['Von']}** bietet Schicht am **{angebot['Datum']}** ({angebot['Zeit']})")
                    c1.caption(f"Grund: {angebot['Grund']}")
                    if c2.button("Übernehmen", key=f"btn_{idx}"):
                        angebot["Status"] = "Übernommen"
                        st.success(f"Du hast die Schicht von {angebot['Von']} übernommen!")
                        st.rerun()

# --- 3. OCR SCANNER (BILD ZU TABELLE) ---
elif auswahl == "📸 Plan hochladen (OCR)":
    st.header("📸 Foto-Upload & Digitalisierung")
    st.info("Lade ein Foto des ausgehängten Plans hoch. Die KI versucht die Texte zu erkennen.")
    
    uploaded_file = st.file_uploader("Bild auswählen...", type=["jpg", "png", "jpeg"])
    
    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        st.image(image, caption="Hochgeladenes Foto", width=400)
        
        if st.button("🔍 Plan jetzt auslesen"):
            with st.spinner("KI analysiert das Bild... (Das kann beim ersten Mal dauern)"):
                try:
                    reader = get_ocr_reader()
                    # Bild in Numpy-Array für EasyOCR umwandeln
                    img_array = np.array(image)
                    result = reader.readtext(img_array)
                    
                    # Texte extrahieren
                    extrahiert = [res[1] for res in result]
                    
                    # Erstelle eine temporäre Tabelle für die Bearbeitung
                    st.session_state.temp_ocr_df = pd.DataFrame({
                        "Datum": ["Bitte eintragen"] * len(extrahiert),
                        "Abteilung": ["Kasse"] * len(extrahiert),
                        "Mitarbeiter_Erkannt": extrahiert,
                        "Zeit": [""] * len(extrahiert)
                    })
                    st.success("Auslesung beendet! Bitte korrigiere die Daten unten.")
                except Exception as e:
                    st.error(f"Fehler bei der OCR: {e}")

        # Editor-Bereich, wenn Daten vorhanden sind
        if "temp_ocr_df" in st.session_state:
            st.subheader("✏️ Manuelle Korrektur & Zuweisung")
            st.write("Die KI hat folgende Texte gefunden. Bitte korrigiere sie für den finalen Plan:")
            
            edited_df = st.data_editor(
                st.session_state.temp_ocr_df, 
                num_rows="dynamic",
                use_container_width=True
            )
            
            if st.button("💾 Final in Datenbank speichern"):
                # Hier führen wir die neuen Daten mit dem bestehenden Plan zusammen
                final_data = edited_df.rename(columns={"Mitarbeiter_Erkannt": "Mitarbeiter"})
                st.session_state.schichten = pd.concat([st.session_state.schichten, final_data], ignore_index=True)
                st.success("Daten wurden zum digitalen Dienstplan hinzugefügt!")
                # Temp-Daten löschen
                del st.session_state.temp_ocr_df
