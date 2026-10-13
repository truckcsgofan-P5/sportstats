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

st.title("⚽🏒 SportStats - Kompletní správa lig")
st.markdown(
    "Aplikace pro správu týmů, zápasů, střelců a automatický výpočet tabulek."
)

# Postranní panel pro navigaci a správu lig
st.sidebar.header("⚙️ Navigace")

# 1. SEKCE PRO VYTVOŘENÍ NOVÉ LIGY
with st.sidebar.expander("➕ Vytvořit novou ligu"):
  new_league_name = st.text_input("Název ligy (např. Serie A)")
  if st.button("Vytvořit ligu"):
    league_clean = new_league_name.strip()
    if league_clean:
      if league_clean not in st.session_state.leagues:
        st.session_state.leagues[league_clean] = {
            "teams": [],
            "matches": pd.DataFrame(
                columns=[
                    "Domácí",
                    "Hosté",
                    "Skóre Domácí",
                    "Skóre Hosté",
                    "Odehráno",
                ]
            ),
            "scorers": pd.DataFrame(columns=["Hráč", "Tým", "Góly"]),
        }
        save_data()
        st.success(f"Liga '{league_clean}' byla vytvořena!")
        st.rerun()
      else:
        st.error("Tato liga již existuje!")
    else:
      st.error("Zadejte název ligy!")

# Výběr aktivní ligy
league_name = st.sidebar.selectbox(
    "Vyberte ligu", list(st.session_state.leagues.keys())
)
current_league = st.session_state.leagues[league_name]

if st.sidebar.button("🔄 Resetovat vše do výchozího stavu"):
  if os.path.exists(DATA_FILE):
    os.remove(DATA_FILE)
  del st.session_state.leagues
  st.rerun()

st.header(f"🏆 {league_name}")

# Hlavní záložky aplikace
tab1, tab2, tab3, tab4 = st.tabs(
    ["📊 Aktuální tabulka", "📅 Zápasy", "⚽ Střelci", "🛡️ Správa týmů"]
)

# 1. TABULKA (automaticky počítaná)
with tab1:
  st.subheader("Tabulka ligy")
  matches_df = current_league["matches"]
  table_data = {}

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

# 2. SPRÁVA ZÁPASŮ
with tab2:
  st.subheader("📅 Zapsat nový zápas")

  teams_list = current_league["teams"]
  if len(teams_list) >= 2:
    with st.form("add_match_form"):
      col1, col2, col3, col4 = st.columns([3, 1, 1, 3])
      with col1:
        home_team = st.selectbox("Domácí tým", teams_list, index=0)
      with col2:
        home_score = st.number_input("Góly dom.", min_value=0, value=0, step=1)
      with col3:
        away_score = st.number_input("Góly hosté", min_value=0, value=0, step=1)
      with col4:
        default_away_idx = 1 if len(teams_list) > 1 else 0
        away_team = st.selectbox(
            "Hostující tým", teams_list, index=default_away_idx
        )

      submitted = st.form_submit_button("➕ Přidat zápas do tabulky")
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
          st.success("Zápas byl úspěšně zapsán!")
          st.rerun()
  else:
    st.warning("Pro zápis zápasů musíte mít v lize zadané alespoň 2 týmy.")

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
  st.subheader("⚽ Přidat střelce gólu")

  teams_list = current_league["teams"]
  if teams_list:
    with st.form("add_scorer_form"):
      col1, col2, col3 = st.columns([2, 2, 1])
      with col1:
        player_name = st.text_input("Jméno hráče")
      with col2:
        player_team = st.selectbox("Tým hráče", teams_list)
      with col3:
        player_goals = st.number_input(
            "Počet gólů", min_value=1, value=1, step=1
        )

      scorer_submitted = st.form_submit_button("➕ Přidat střelce")
      if scorer_submitted:
        if not player_name.strip():
          st.error("Zadejte jméno hráče!")
        else:
          new_scorer = pd.DataFrame([{
              "Hráč": player_name.strip(),
              "Tým": player_team,
              "Góly": int(player_goals),
          }])
          current_league["scorers"] = pd.concat(
              [current_league["scorers"], new_scorer], ignore_index=True
          )
          save_data()
          st.success(f"Hráč {player_name} byl přidán do tabulky střelců!")
          st.rerun()
  else:
    st.warning("Nejprve přidejte týmy v záložce 'Správa týmů'.")

  st.divider()
  st.subheader("Žebříček střelců (možnost úpravy)")
  edited_scorers = st.data_editor(
      current_league["scorers"],
      num_rows="dynamic",
      key=f"scorers_editor_{league_name}",
      use_container_width=True,
  )
  if not current_league["scorers"].equals(edited_scorers):
    current_league["scorers"] = edited_scorers
    save_data()

# 4. SPRÁVA TÝMŮ
with tab4:
  st.subheader("🛡️ Seznam týmů v lize")

  col_add, col_list = st.columns([1, 1])

  with col_add:
    st.markdown("**Přidat nový tým:**")
    with st.form("add_team_form"):
      new_team = st.text_input("Název nového týmu")
      add_team_btn = st.form_submit_button("Přidat tým")
      if add_team_btn:
        if not new_team.strip():
          st.error("Název týmu nemůže být prázdný!")
        elif new_team in current_league["teams"]:
          st.error("Tento tým již v lize existuje!")
        else:
          current_league["teams"].append(new_team.strip())
          save_data()
          st.success(f"Tým '{new_team}' byl přidán!")
          st.rerun()

  with col_list:
    st.markdown("**Aktuální týmy:**")
    if current_league["teams"]:
      teams_df = pd.DataFrame({"Tým": current_league["teams"]})
      st.dataframe(teams_df, use_container_width=True, hide_index=True)

      st.markdown("---")
      team_to_delete = st.selectbox(
          "Vyberte tým k odstranění", current_league["teams"]
      )
      if st.button("🗑️ Smazat vybraný tým", type="primary"):
        current_league["teams"].remove(team_to_delete)
        save_data()
        st.success(f"Tým '{team_to_delete}' byl smazán.")
        st.rerun()
    else:
      st.info("V lize nejsou žádné týmy.")
