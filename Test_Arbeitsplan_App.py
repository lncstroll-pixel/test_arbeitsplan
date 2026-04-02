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

# --- LOGIK FÜR ZEILEN-ERKENNUNG ---
def verarbeite_tabelle(ocr_result):
    if not ocr_result:
        return []

    # Sortiere alle Funde nach der Y-Koordinate (von oben nach unten)
    ocr_result.sort(key=lambda x: x[0][0][1])

    rows = []
    current_row = []
    last_y = ocr_result[0][0][0][1]
    y_threshold = 25  # Pixel-Toleranz für eine Zeile

    for res in ocr_result:
        bbox, text, prob = res
        y_top = bbox[0][1]
        x_left = bbox[0][0]

        if abs(y_top - last_y) > y_threshold:
            current_row.sort(key=lambda x: x[0])
            rows.append([item[1] for item in current_row])
            current_row = []
            last_y = y_top
        
        current_row.append((x_left, text))

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
        # Anzeige der flachen Liste (Datenbank-Stil)
        st.dataframe(st.session_state.schichten, use_container_width=True, hide_index=True)

# --- 2. VERBESSERTER OCR SCANNER (MIT WOCHENTAG-SPALTEN) ---
elif auswahl == "📸 Plan hochladen (OCR)":
    st.header("📸 Intelligente Tabellen-Erkennung")
    st.write("Die KI ordnet erkannte Zeiten direkt den Wochentagen zu.")
    
    uploaded_file = st.file_uploader("Bild oder Screenshot hochladen...", type=["jpg", "png", "jpeg"])
    
    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        st.image(image, caption="Vorschau", width=500)
        
        if st.button("🔍 Plan analysieren"):
            with st.spinner("KI extrahiert Daten in Tabellenform..."):
                reader = get_ocr_reader()
                result = reader.readtext(np.array(image))
                
                # Zeilenweise Strukturierung
                strukturierte_zeilen = verarbeite_tabelle(result)
                
                # Definition der festen Spalten
                spalten = ["Mitarbeiter", "Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"]
                final_rows = []

                for zeile in strukturierte_zeilen:
                    # Wir erstellen ein leeres Wörterbuch für die Zeile
                    new_row = {s: "" for s in spalten}
                    
                    if len(zeile) > 0:
                        # Erstes erkanntes Element der Zeile = Mitarbeitername
                        new_row["Mitarbeiter"] = zeile[0]
                        
                        # Die restlichen Elemente werden den Tagen Mo-So zugeordnet
                        for i, schicht_text in enumerate(zeile[1:]):
                            if i < 7: # Begrenzung auf 7 Tage
                                tag_name = spalten[i+1]
                                new_row[tag_name] = schicht_text
                        
                        # Nur Zeilen hinzufügen, die nicht leer sind
                        if new_row["Mitarbeiter"]:
                            final_rows.append(new_row)

                st.session_state.temp_df = pd.DataFrame(final_rows)

        if "temp_df" in st.session_state:
            st.subheader("✏️ Ergebnis prüfen & korrigieren")
            st.info("Hier kannst du Zeiten einfach korrigieren oder in die richtige Spalte verschieben.")
            
            # Editor zeigt jetzt die Mo-So Matrix an
            edited_df = st.data_editor(
                st.session_state.temp_df,
                use_container_width=True,
                num_rows="dynamic"
            )
            
            if st.button("💾 In Dienstplan übernehmen"):
                # Konvertierung der Matrix zurück in die Datenbank-Liste
                neue_eintraege = []
                wochentage = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"]
                
                for _, row in edited_df.iterrows():
                    for tag in wochentage:
                        zeit_wert = str(row[tag]).strip()
                        # Nur speichern, wenn ein Text/Zeit in der Zelle steht
                        if zeit_wert and zeit_wert != "nan" and zeit_wert != "":
                            neue_eintraege.append({
                                "Datum": tag, 
                                "Abteilung": "Zuweisen...",
                                "Mitarbeiter": row["Mitarbeiter"],
                                "Zeit": zeit_wert
                            })
                
                if neue_eintraege:
                    neuer_df = pd.DataFrame(neue_eintraege)
                    st.session_state.schichten = pd.concat([st.session_state.schichten, neuer_df], ignore_index=True)
                    st.success(f"{len(neue_eintraege)} Schichten erfolgreich gespeichert!")
                    del st.session_state.temp_df
                    st.rerun()
                else:
                    st.warning("Keine Daten zum Speichern gefunden.")
