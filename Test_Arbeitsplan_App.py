import streamlit as st
import pandas as pd
import numpy as np
import easyocr
from PIL import Image
from datetime import datetime

# --- SEITENKONFIGURATION ---
st.set_page_config(page_title="Studi-Schicht-Hub", page_icon="📅", layout="wide")

# --- INITIALISIERUNG DER DATENBANK ---
if "schichten" not in st.session_state:
    st.session_state.schichten = pd.DataFrame(columns=["Datum", "Abteilung", "Mitarbeiter", "Zeit"])

@st.cache_resource
def get_ocr_reader():
    return easyocr.Reader(['de'])

# --- NEU: VERBESSERTE LOGIK FÜR ZEILEN-ERKENNUNG ---
def verarbeite_tabelle(ocr_result):
    if not ocr_result:
        return []

    # 1. Sortiere alle Funde nach der Y-Koordinate (von oben nach unten)
    ocr_result.sort(key=lambda x: x[0][0][1])

    rows = []
    current_row = []
    last_y = ocr_result[0][0][0][1]
    y_threshold = 25  # Toleranz in Pixeln: Was auf einer Höhe liegt, ist eine Zeile

    for res in ocr_result:
        bbox, text, prob = res
        y_top = bbox[0][1]
        x_left = bbox[0][0]

        # Wenn der Text deutlich tiefer liegt als der letzte -> Neue Zeile starten
        if abs(y_top - last_y) > y_threshold:
            # Bevor wir die Zeile speichern, sortieren wir sie von links nach rechts (X-Achse)
            current_row.sort(key=lambda x: x[0])
            rows.append([item[1] for item in current_row])
            current_row = []
            last_y = y_top
        
        current_row.append((x_left, text))

    # Letzte Zeile nicht vergessen
    if current_row:
        current_row.sort(key=lambda x: x[0])
        rows.append([item[1] for item in current_row])
    
    return rows

# --- NAVIGATION ---
st.sidebar.title("📌 Menü")
auswahl = st.sidebar.radio("Gehe zu:", ["📅 Dienstplan", "📸 Plan hochladen (OCR)"])

# --- 1. DIENSTPLAN ANZEIGE ---
if auswahl == "📅 Dienstplan":
    st.header("📅 Aktueller Arbeitsplan")
    if st.session_state.schichten.empty:
        st.info("Noch keine Daten vorhanden. Lade einen Plan unter 'OCR' hoch!")
    else:
        st.dataframe(st.session_state.schichten, use_container_width=True, hide_index=True)

# --- 2. VERBESSERTER OCR SCANNER ---
elif auswahl == "📸 Plan hochladen (OCR)":
    st.header("📸 Intelligente Tabellen-Erkennung")
    st.write("Diese Version sortiert die Funde nach Zeilen und Spalten.")
    
    uploaded_file = st.file_uploader("Bild oder Screenshot hochladen...", type=["jpg", "png", "jpeg"])
    
    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        st.image(image, caption="Vorschau", width=500)
        
        if st.button("🔍 Plan analysieren"):
            with st.spinner("KI sortiert Zeilen und Spalten..."):
                reader = get_ocr_reader()
                result = reader.readtext(np.array(image))
                
                # Nutze die neue Koordinaten-Logik
                strukturierte_zeilen = verarbeite_tabelle(result)
                
                # Wir bereiten die Daten für den Editor auf
                formatiert = []
                for zeile in strukturierte_zeilen:
                    # Wir versuchen, den Namen (erstes Element) und die Zeit zu trennen
                    name = zeile[0] if len(zeile) > 0 else ""
                    rest = " | ".join(zeile[1:]) if len(zeile) > 1 else ""
                    formatiert.append({"Mitarbeiter": name, "Erkannte_Daten": rest, "Wochentag": "Montag"})

                st.session_state.temp_df = pd.DataFrame(formatiert)

        if "temp_df" in st.session_state:
            st.subheader("✏️ Ergebnis prüfen")
            st.info("Klicke in die Zellen, um Fehler der KI direkt zu korrigieren.")
            
            # Editor mit Dropdown für Wochentage
            edited_df = st.data_editor(
                st.session_state.temp_df,
                column_config={
                    "Wochentag": st.column_config.SelectboxColumn(
                        "Wochentag",
                        options=["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"]
                    )
                },
                num_rows="dynamic",
                use_container_width=True
            )
            
            if st.button("💾 In Dienstplan übernehmen"):
                # Umwandeln in das Hauptformat
                neue_daten = edited_df[["Wochentag", "Mitarbeiter", "Erkannte_Daten"]].rename(
                    columns={"Wochentag": "Datum", "Erkannte_Daten": "Zeit"}
                )
                neue_daten["Abteilung"] = "Zuweisen..."
                
                st.session_state.schichten = pd.concat([st.session_state.schichten, neue_daten], ignore_index=True)
                st.success("Daten gespeichert!")
                del st.session_state.temp_df
