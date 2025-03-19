import streamlit as st
import requests
import json

# -------------------------------------------
# 1) Streamlit Page Config
# -------------------------------------------
st.set_page_config(
    page_title="OKR Dashboard (Tech-Background, Ampelsystem)",
    page_icon="✅",
    layout="wide"
)

# -------------------------------------------
# 2) Custom CSS (Moderner, animierter Gradient + Google Font)
# -------------------------------------------
custom_css = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;700&display=swap');

/* Animierter Gradient (dynamischer Hintergrund) */
body, .block-container {
    background: linear-gradient(-45deg, #1E1F31, #34344E, #1E1F31, #2A2B45);
    background-size: 400% 400%;
    animation: animatedGradient 15s ease infinite;
    color: #F0F0F0 !important;
    font-family: 'Roboto', sans-serif;
    margin: 0;
    padding: 0;
}

@keyframes animatedGradient {
    0% { background-position: 0% 50%; }
    50% { background-position: 100% 50%; }
    100% { background-position: 0% 50%; }
}

/* Kategorie-Überschrift etwas größer */
.category-heading {
    font-size: 1.4rem;
    font-weight: bold;
    margin-top: 2rem;
    margin-bottom: 1rem;
}

h1, h2, h3, h4 {
    color: #FFFFFF !important;
    text-shadow: none !important;
}

.block-container {
    padding: 2rem 2rem 2rem 2rem;
}

/* Sidebar: dunkler Hintergrund */
[data-testid="stSidebar"] {
    background-color: #1E1E1E;
}

/* Button-Hover */
button:hover {
    box-shadow: 0 0 10px #03DAC6;
    transition: 0.3s;
}

/* Eigener Scrollbalken */
::-webkit-scrollbar {
    width: 8px;
}
::-webkit-scrollbar-thumb {
    background-color: #03DAC6;
    border-radius: 4px;
}

/* Fortschrittsbalken-Container */
.progress-container {
    background-color: #2A2A2A;
    border-radius: 10px;
    margin: 0.5rem 0;
    padding: 0.25rem;
    box-shadow: 0 2px 8px rgba(0,0,0,0.3);
}

/* Innerer Balken: Ampelfarbe dynamisch */
.progress-bar {
    height: 20px;
    border-radius: 8px;
    text-align: center;
    color: #000;
    font-weight: bold;
    transition: width 0.4s ease;
}
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# -------------------------------------------
# 3) Ampelsystem-Farbe für Fortschrittsbalken
# -------------------------------------------
def get_ampel_color(percentage: float) -> str:
    if percentage < 30:
        return "#e63946"  # Rot
    elif percentage < 70:
        return "#ffb703"  # Orange
    else:
        return "#06d6a0"  # Grün

def render_progress_bar(percentage: float) -> str:
    percentage = min(max(percentage, 0), 100)
    color = get_ampel_color(percentage)
    return f"""
    <div class="progress-container">
      <div class="progress-bar" style="width:{percentage:.1f}%; min-width:30px; background-color:{color};">
        {percentage:.1f}%
      </div>
    </div>
    """

# -------------------------------------------
# 4) Gist-Lade- und Speicherfunktionen
# -------------------------------------------
def load_data_from_gist():
    token = st.secrets["GITHUB_TOKEN"]
    gist_id = st.secrets["GIST_ID"]
    gist_url = f"https://api.github.com/gists/{gist_id}"

    headers = {"Authorization": f"token {token}"}
    response = requests.get(gist_url, headers=headers)
    response.raise_for_status()

    gist_data = response.json()
    files = gist_data.get("files", {})
    if "okr_data.json" not in files:
        st.warning("Fehlt: 'okr_data.json' im Gist.")
        return []
    
    content = files["okr_data.json"]["content"]
    try:
        return json.loads(content)
    except Exception as e:
        st.error(f"Fehler beim JSON-Parsing: {e}")
        return []

def save_data_to_gist(okr_data):
    token = st.secrets["GITHUB_TOKEN"]
    gist_id = st.secrets["GIST_ID"]
    gist_url = f"https://api.github.com/gists/{gist_id}"

    headers = {"Authorization": f"token {token}"}
    updated_content = json.dumps(okr_data, indent=2, ensure_ascii=False)
    payload = {
        "files": {
            "okr_data.json": {
                "content": updated_content
            }
        }
    }
    response = requests.patch(gist_url, headers=headers, data=json.dumps(payload))
    response.raise_for_status()

# -------------------------------------------
# 5) Session-State initialisieren
# -------------------------------------------
if "okr_data" not in st.session_state:
    try:
        st.session_state.okr_data = load_data_from_gist()
    except Exception as e:
        st.error(f"Fehler beim Laden aus Gist: {e}")
        st.session_state.okr_data = []

# -------------------------------------------
# 6) Dashboard-Seite
# -------------------------------------------
def show_dashboard():
    st.title("OKR Dashboard – Animierter Hintergrund, Ampelsystem")

    if not st.session_state.okr_data:
        st.info("Keine OKR-Daten vorhanden. Füge welche hinzu oder prüfe deinen Gist.")
        return

    for cat_i, cat in enumerate(st.session_state.okr_data):
        st.markdown(f"<div class='category-heading'>{cat['category_name']}</div>", unsafe_allow_html=True)

        for obj_i, obj in enumerate(cat["objectives"]):

            # Falls auto_update=True -> current_value = Anzahl items
            if obj.get("auto_update", False):
                obj["current_value"] = float(len(obj["items"]))

            # Zwei Spalten (Name, Balken & Neueintrag links // Einträge rechts)
            col_left, col_right = st.columns([3, 2])

            with col_left:
                # -- Name und Balken
                st.markdown(f"**{obj['name']}**")
                current = obj["current_value"]
                target = obj["target_value"]
                progress_percent = (current / target * 100) if target else 0
                bar_html = render_progress_bar(progress_percent)
                st.markdown(bar_html, unsafe_allow_html=True)
                st.markdown(f"{int(current)} / {int(target)} &nbsp; ({progress_percent:.1f}%)")

                # -- "Neuen Eintrag hinzufügen" (nur, wenn use_list=True)
                if obj.get("use_list", False):
                    st.markdown("#### Neuen Eintrag hinzufügen")
                    new_item_key = f"item_input_{cat_i}_{obj_i}"
                    new_item = st.text_input("", key=new_item_key, placeholder="Neuer Eintrag ...")
                    add_btn_key = f"add_btn_{cat_i}_{obj_i}"
                    if st.button("Hinzufügen", key=add_btn_key):
                        if new_item.strip():
                            obj["items"].append(new_item.strip())
                            if obj.get("auto_update", False):
                                obj["current_value"] = float(len(obj["items"]))
                            save_data_to_gist(st.session_state.okr_data)
                            st.experimental_rerun()

            with col_right:
                # -- Liste der Einträge (nur, wenn use_list=True)
                if obj.get("use_list", False) and obj["items"]:
                    st.markdown("#### Bereits erfasste Einträge:")
                    for idx, entry in enumerate(obj["items"]):
                        st.write(f"{idx+1}) {entry}")
                        col_e, col_d = st.columns([1,1])

                        # Bearbeiten
                        with col_e:
                            edit_key = f"edit_btn_{cat_i}_{obj_i}_{idx}"
                            if st.button("Bearbeiten", key=edit_key):
                                new_val = st.text_input("Bearbeite Eintrag", value=entry, key=f"edit_field_{cat_i}_{obj_i}_{idx}")
                                if st.button("Speichern", key=f"save_{cat_i}_{obj_i}_{idx}"):
                                    obj["items"][idx] = new_val
                                    if obj.get("auto_update", False):
                                        obj["current_value"] = float(len(obj["items"]))
                                    save_data_to_gist(st.session_state.okr_data)
                                    st.experimental_rerun()

                        # Löschen
                        with col_d:
                            delete_key = f"del_btn_{cat_i}_{obj_i}_{idx}"
                            if st.button("Löschen", key=delete_key):
                                obj["items"].pop(idx)
                                if obj.get("auto_update", False):
                                    obj["current_value"] = float(len(obj["items"]))
                                save_data_to_gist(st.session_state.okr_data)
                                st.experimental_rerun()

            st.write("---")

# -------------------------------------------
# 7) Update-Seite
# -------------------------------------------
def show_update_page():
    st.title("OKRs aktualisieren")

    if not st.session_state.okr_data:
        st.info("Keine Daten vorhanden.")
        return

    for cat_i, cat in enumerate(st.session_state.okr_data):
        st.markdown(f"## {cat['category_name']}")
        for obj_i, obj in enumerate(cat["objectives"]):
            obj["name"] = st.text_input(
                f"Name (#{obj_i+1})",
                value=obj["name"],
                key=f"name_{cat_i}_{obj_i}"
            )

            # current_value, nur editierbar wenn auto_update=False
            if obj.get("auto_update", False):
                st.write(f"**Aktueller Wert (Auto-Update):** {int(obj['current_value'])}")
            else:
                obj["current_value"] = st.number_input(
                    f"Aktueller Wert (#{obj_i+1})",
                    min_value=0.0,
                    value=float(obj["current_value"]),
                    step=1.0,
                    key=f"current_{cat_i}_{obj_i}"
                )

            obj["target_value"] = st.number_input(
                f"Zielwert (#{obj_i+1})",
                min_value=0.0,
                value=float(obj["target_value"]),
                step=1.0,
                key=f"target_{cat_i}_{obj_i}"
            )

            # Checkbox: Liste ja/nein
            obj["use_list"] = st.checkbox(
                f"Liste aktivieren? (#{obj_i+1})",
                value=obj.get("use_list", False),
                key=f"use_list_{cat_i}_{obj_i}"
            )

            # Checkbox: auto_update
            obj["auto_update"] = st.checkbox(
                f"Auto-Update? (#{obj_i+1}) => current_value = Anzahl Einträge",
                value=obj.get("auto_update", False),
                key=f"auto_update_{cat_i}_{obj_i}"
            )

        st.write("---")

    if st.button("Änderungen speichern"):
        save_data_to_gist(st.session_state.okr_data)
        st.success("Änderungen wurden gespeichert.")

    if st.button("Neue Kategorie hinzufügen"):
        st.session_state.okr_data.append({
            "category_name": "Neue Kategorie",
            "objectives": []
        })
        save_data_to_gist(st.session_state.okr_data)
        st.experimental_rerun()

# -------------------------------------------
# 8) Navigation
# -------------------------------------------
page = st.sidebar.selectbox("Navigation", ["Dashboard", "Update OKRs"])

if page == "Dashboard":
    show_dashboard()
elif page == "Update OKRs":
    show_update_page()
