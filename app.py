import json
import os
import pandas as pd
import streamlit as st

# Nastavení stránky
st.set_page_config(
    page_title="SportStats - Aplikace", page_icon="⚽", layout="wide"
)

DATA_FILE = "sports_data.json"


# Funkce pro načtení dat ze souboru
def load_data():
  if os.path.exists(DATA_FILE):
    try:
      with open(DATA_FILE, "r", encoding="utf-8") as f:
        raw_data = json.load(f)
      loaded = {}
      for league, content in raw_data.items():
        loaded[league] = {
            "teams": content.get("teams", []),
            "matches": pd.DataFrame(content["matches"]),
            "scorers": pd.DataFrame(content["scorers"]),
        }
      return loaded
    except Exception:
      return get_default_data()
  return get_default_data()


# Výchozí data, pokud soubor ještě neexistuje
def get_default_data():
  return {
      "Premier League (Anglie)": {
          "teams": [
              "Manchester City",
              "Arsenal",
              "Liverpool",
              "Chelsea",
              "Manchester United",
              "Tottenham",
              "Newcastle",
              "Aston Villa",
          ],
          "matches": pd.DataFrame([
              {
                  "Domácí": "Manchester City",
                  "Hosté": "Arsenal",
                  "Skóre Domácí": 2,
                  "Skóre Hosté": 2,
                  "Odehráno": True,
              },
              {
                  "Domácí": "Liverpool",
                  "Hosté": "Chelsea",
                  "Skóre Domácí": 3,
                  "Skóre Hosté": 1,
                  "Odehráno": True,
              },
          ]),
          "scorers": pd.DataFrame([
              {"Hráč": "Erling Haaland", "Tým": "Manchester City", "Góly": 10},
              {"Hráč": "Cole Palmer", "Tým": "Chelsea", "Góly": 7},
          ]),
      },
      "La Liga (Španělsko)": {
          "teams": [
              "Real Madrid",
              "Barcelona",
              "Atletico Madrid",
              "Villarreal",
              "Sevilla",
              "Valencia",
          ],
          "matches": pd.DataFrame([
              {
                  "Domácí": "Real Madrid",
                  "Hosté": "Barcelona",
                  "Skóre Domácí": 2,
                  "Skóre Hosté": 1,
                  "Odehráno": True,
              }
          ]),
          "scorers": pd.DataFrame([
              {"Hráč": "Kylian Mbappé", "Tým": "Real Madrid", "Góly": 9},
              {"Hráč": "Robert Lewandowski", "Tým": "Barcelona", "Góly": 8},
          ]),
      },
  }


# Funkce pro uložení dat do souboru
def save_data():
  data_to_save = {}
  for league, content in st.session_state.leagues.items():
    data_to_save[league] = {
        "teams": content["teams"],
        "matches": content["matches"].to_dict("records"),
        "scorers": content["scorers"].to_dict("records"),
    }
  with open(DATA_FILE, "w", encoding="utf-8") as f:
    json.dump(data_to_save, f, ensure_ascii=False, indent=4)


# Inicializace stavu
if "leagues" not in st.session_state:
  st.session_state.leagues = load_data()

st.title("⚽🏒 SportStats - Trvalá správa lig a výsledků")
st.markdown(
    "Data se ukládají automaticky. Zápasy můžete pohodlně přidávat přes"
    " formulář s výběrem týmů."
)

# Postranní panel pro výběr ligy
st.sidebar.header("⚙️ Navigace")
league_name = st.sidebar.selectbox(
    "Vyberte ligu", list(st.session_state.leagues.keys())
)
current_league = st.session_state.leagues[league_name]

# Správa týmů v postranním panelu
with st.sidebar.expander("➕ Přidat nový tým do ligy"):
  new_team_name = st.text_input("Název týmu")
  if st.button("Přidat tým"):
    if new_team_name and new_team_name not in current_league["teams"]:
      current_league["teams"].append(new_team_name)
      save_data()
      st.success(f"Tým {new_team_name} byl přidán!")
      st.rerun()
    else:
      st.error("Tým již existuje nebo je prázdný.")

if st.sidebar.button("🔄 Resetovat vše do výchozího stavu"):
  if os.path.exists(DATA_FILE):
    os.remove(DATA_FILE)
  del st.session_state.leagues
  st.rerun()

st.header(f"🏆 {league_name}")

# Záložky v aplikaci
tab1, tab2, tab3 = st.tabs(["📊 Aktuální tabulka", "📅 Zápasy", "⚽ Střelci"])

# 1. TABULKA (automaticky počítaná)
with tab1:
  st.subheader("Tabulka ligy")
  matches_df = current_league["matches"]
  table_data = {}

  # Inicializujeme všechny týmy v tabulce s 0, aby byly vidět i ty, co ještě nehrály
  for team in current_league["teams"]:
    table_data[team] = {
        "Zápasy": 0,
        "Výhry": 0,
        "Remízy": 0,
        "Prohry": 0,
        "Vstřelené": 0,
        "Obdržené": 0,
        "Body": 0,
    }

  if not matches_df.empty:
    for _, row in matches_df.iterrows():
      if row.get("Odehráno", True):
        home = row["Domácí"]
        away = row["Hosté"]
        try:
          hs = int(row["Skóre Domácí"])
          as_ = int(row["Skóre Hosté"])
        except (ValueError, TypeError):
          continue

        for team in [home, away]:
          if team not in table_data:
            table_data[team] = {
                "Zápasy": 0,
                "Výhry": 0,
                "Remízy": 0,
                "Prohry": 0,
                "Vstřelené": 0,
                "Obdržené": 0,
                "Body": 0,
            }

        table_data[home]["Zápasy"] += 1
        table_data[away]["Zápasy"] += 1
        table_data[home]["Vstřelené"] += hs
        table_data[home]["Obdržené"] += as_
        table_data[away]["Vstřelené"] += as_
        table_data[away]["Obdržené"] += hs

        if hs > as_:
          table_data[home]["Výhry"] += 1
          table_data[home]["Body"] += 3
          table_data[away]["Prohry"] += 1
        elif hs < as_:
          table_data[away]["Výhry"] += 1
          table_data[away]["Body"] += 3
          table_data[home]["Prohry"] += 1
        else:
          table_data[home]["Remízy"] += 1
          table_data[home]["Body"] += 1
          table_data[away]["Remízy"] += 1
          table_data[away]["Body"] += 1

  standings_list = []
  for team, stats in table_data.items():
    gd = stats["Vstřelené"] - stats["Obdržené"]
    standings_list.append({
        "Tým": team,
        "Z": stats["Zápasy"],
        "V": stats["Výhry"],
        "R": stats["Remízy"],
        "P": stats["Prohry"],
        "Skóre": f"{stats['Vstřelené']}:{stats['Obdržené']}",
        "GD": gd,
        "Body": stats["Body"],
        "Vstřelené": stats["Vstřelené"],
    })

  standings_df = pd.DataFrame(standings_list).sort_values(
      by=["Body", "GD", "Vstřelené"], ascending=False
  )
  standings_df = standings_df.drop(columns=["Vstřelené"])
  standings_df.reset_index(drop=True, inplace=True)
  standings_df.index += 1
  st.dataframe(standings_df, use_container_width=True)

# 2. SPRÁVA ZÁPASŮ (S formulářem pro výběr týmů)
with tab2:
  st.subheader("📅 Přidat nový zápas")

  teams_list = current_league["teams"]
  if len(teams_list) >= 2:
    with st.form("add_match_form"):
      col1, col2, col3, col4 = st.columns([3, 1, 1, 2])
      with col1:
        home_team = st.selectbox("Domácí tým", teams_list, index=0)
      with col2:
        home_score = st.number_input("Góly dom.", min_value=0, value=0, step=1)
      with col3:
        away_score = st.number_input("Góly hosté", min_value=0, value=0, step=1)
      with col4:
        # Vybereme druhý tým jako výchozí, pokud existuje
        default_away_idx = 1 if len(teams_list) > 1 else 0
        away_team = st.selectbox(
            "Hostující tým", teams_list, index=default_away_idx
        )

      submitted = st.form_submit_button("➕ Zapsat zápas")
      if submitted:
        if home_team == away_team:
          st.error("Domácí a hostující tým nemůže být stejný!")
        else:
          new_row = pd.DataFrame([{
              "Domácí": home_team,
              "Hosté": away_team,
              "Skóre Domácí": int(home_score),
              "Skóre Hosté": int(away_score),
              "Odehráno": True,
          }])
          current_league["matches"] = pd.concat(
              [current_league["matches"], new_row], ignore_index=True
          )
          save_data()
          st.success("Zápas byl úspěšně zapsán a tabulka se přepočítala!")
          st.rerun()
  else:
    st.warning("Pro přidání zápasu musíte mít v lize zadané alespoň 2 týmy.")

  st.divider()
  st.subheader("Seznam odehraných zápasů (možnost úpravy)")
  edited_matches = st.data_editor(
      current_league["matches"],
      num_rows="dynamic",
      key=f"matches_editor_{league_name}",
      use_container_width=True,
  )
  if not current_league["matches"].equals(edited_matches):
    current_league["matches"] = edited_matches
    save_data()

# 3. SPRÁVA STŘELCŮ
with tab3:
  st.subheader("⚽ Top střelci")
  st.markdown("Zde můžete upravovat góly střelců nebo přidávat nové.")

  edited_scorers = st.data_editor(
      current_league["scorers"],
      num_rows="dynamic",
      key=f"scorers_editor_{league_name}",
      use_container_width=True,
  )
  if not current_league["scorers"].equals(edited_scorers):
    current_league["scorers"] = edited_scorers
    save_data()
