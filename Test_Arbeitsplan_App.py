import streamlit as st
import pandas as pd
import numpy as np
import easyocr
from PIL import Image

# --- SEITENKONFIGURATION ---
st.set_page_config(page_title="Studi-Schicht-Hub", page_icon="📅", layout="wide")

if "schichten" not in st.session_state:
    st.session_state.schichten = pd.DataFrame(columns=["Datum", "Abteilung", "Mitarbeiter", "Zeit"])

@st.cache_resource
def get_ocr_reader():
    return easyocr.Reader(['de'])

def verarbeite_tabelle(ocr_result):
    if not ocr_result:
        return []
    
    # Sortieren nach Y (oben nach unten)
    ocr_result.sort(key=lambda x: x[0][0][1])
    
    rows = []
    current_row = []
    last_y = ocr_result[0][0][0][1]
    y_threshold = 25 

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

if auswahl == "📅 Dienstplan":
    st.header("📅 Aktueller Arbeitsplan")
    st.dataframe(st.session_state.schichten, use_container_width=True, hide_index=True)

elif auswahl == "📸 Plan hochladen (OCR)":
    st.header("📸 Intelligente Tabellen-Erkennung")
    
    uploaded_file = st.file_uploader("Bild hochladen...", type=["jpg", "png", "jpeg"])
    
    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        st.image(image, caption="Vorschau", width=500)
        
        if st.button("🔍 Plan analysieren"):
            with st.spinner("KI bereinigt Tabellenstruktur..."):
                reader = get_ocr_reader()
                result = reader.readtext(np.array(image))
                strukturierte_zeilen = verarbeite_tabelle(result)
                
                spalten = ["Mitarbeiter", "Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"]
                wochentage_liste = ["montag", "dienstag", "mittwoch", "donnerstag", "freitag", "samstag", "sonntag"]
                final_rows = []

                for zeile in strukturierte_zeilen:
                    # SCHRITT 1: Prüfen, ob die Zeile nur Wochentage enthält (Überschrift im Bild)
                    # Wir prüfen das erste Element. Wenn es "Montag" etc. ist, überspringen wir die Zeile.
                    erstes_wort = zeile[0].lower() if len(zeile) > 0 else ""
                    if erstes_wort in wochentage_liste or "datum" in erstes_wort:
                        continue
                    
                    # SCHRITT 2: Zeile zuordnen
                    new_row = {s: "" for s in spalten}
                    if len(zeile) > 0:
                        new_row["Mitarbeiter"] = zeile[0]
                        
                        # Wir versuchen, Zeit-Fragmente zu verbinden (z.B. "10.00" und "20.00" -> "10:00-20:00")
                        reine_zeiten = zeile[1:]
                        tag_index = 1
                        for i in range(len(reine_zeiten)):
                            if tag_index < len(spalten):
                                # Wenn das aktuelle Element eine Zeit ist und das nächste auch, evtl. verbinden?
                                # Hier halten wir es simpel: Ein Element pro Tag-Spalte
                                new_row[spalten[tag_index]] = reine_zeiten[i]
                                tag_index += 1
                        
                        if new_row["Mitarbeiter"]:
                            final_rows.append(new_row)

                st.session_state.temp_df = pd.DataFrame(final_rows)

        if "temp_df" in st.session_state:
            st.subheader("✏️ Ergebnis prüfen & korrigieren")
            edited_df = st.data_editor(st.session_state.temp_df, use_container_width=True, num_rows="dynamic")
            
            if st.button("💾 In Dienstplan übernehmen"):
                neue_eintraege = []
                for _, row in edited_df.iterrows():
                    for tag in ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"]:
                        zeit = str(row[tag]).strip()
                        if zeit and zeit.lower() != "nan" and zeit != "":
                            neue_eintraege.append({
                                "Datum": tag, 
                                "Abteilung": "Zuweisen...",
                                "Mitarbeiter": row["Mitarbeiter"],
                                "Zeit": zeit
                            })
                
                if neue_eintraege:
                    st.session_state.schichten = pd.concat([st.session_state.schichten, pd.DataFrame(neue_eintraege)], ignore_index=True)
                    st.success("Übertragen!")
                    del st.session_state.temp_df
                    st.rerun()
