import base64
import json
import os
import pandas as pd
import requests
import streamlit as st

# Nastavení stránky
st.set_page_config(
    page_title="SportStats - Aplikace", page_icon="⚽", layout="wide"
)

# Konfigurace pro GitHub API
HAS_GITHUB = "GITHUB_TOKEN" in st.secrets and "GITHUB_REPO" in st.secrets
GITHUB_TOKEN = st.secrets.get("GITHUB_TOKEN", "")
GITHUB_REPO = st.secrets.get("GITHUB_REPO", "")
FILE_PATH = "sports_data.json"


# Výchozí data
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


# Funkce pro načtení dat (s hlášením chyb)
def load_data(show_messages=False):
  if HAS_GITHUB:
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{FILE_PATH}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
        "Cache-Control": "no-cache",
    }
    try:
      response = requests.get(url, headers=headers)
      if response.status_code == 200:
        content_file = response.json()
        file_content_bytes = base64.b64decode(content_file["content"])
        raw_data = json.loads(file_content_bytes.decode("utf-8"))

        loaded = {}
        for league, content in raw_data.items():
          loaded[league] = {
              "teams": content.get("teams", []),
              "matches": pd.DataFrame(content["matches"]),
              "scorers": pd.DataFrame(content["scorers"]),
          }
        if show_messages:
          st.success("Data byla úspěšně stažena z GitHubu!")
        return loaded
      elif response.status_code == 404:
        if show_messages:
          st.warning(
              "Soubor `sports_data.json` ještě na GitHubu neexistuje. Jakmile"
              " cokoliv v aplikaci uložite, automaticky se vytvoří."
          )
      else:
        if show_messages:
          st.error(
              f"Chyba při komunikaci s GitHubem (Kód: {response.status_code})."
              " Zkontrolujte token."
          )
    except Exception as e:
      if show_messages:
        st.error(f"Nastala výjimka: {e}")
  else:
    if show_messages:
      st.warning(
          "Není nastaveno GitHub API v Secrets, používá se lokální režim."
      )
    if os.path.exists(FILE_PATH):
      try:
        with open(FILE_PATH, "r", encoding="utf-8") as f:
          raw_data = json.load(f)
        loaded = {}
        for league, content in raw_data.items():
          loaded[league] = {
              "teams": content.get("teams", []),
              "matches": pd.DataFrame(content["matches"]),
              "scorers": pd.DataFrame(content["scorers"]),
          }
        if show_messages:
          st.success("Data načtena z lokálního souboru!")
        return loaded
      except Exception as e:
        if show_messages:
          st.error(f"Chyba při čtení lokálního souboru: {e}")

  return get_default_data()


# Funkce pro uložení dat
def save_data():
  data_to_save = {}
  for league, content in st.session_state.leagues.items():
    data_to_save[league] = {
        "teams": content["teams"],
        "matches": content["matches"].to_dict("records"),
        "scorers": content["scorers"].to_dict("records"),
    }

  if HAS_GITHUB:
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{FILE_PATH}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
    }

    json_str = json.dumps(data_to_save, ensure_ascii=False, indent=4)
    encoded_content = base64.b64encode(json_str.encode("utf-8")).decode(
        "utf-8"
    )

    sha = None
    get_resp = requests.get(url, headers=headers)
    if get_resp.status_code == 200:
      sha = get_resp.json().get("sha")

    payload = {
        "message": "Aktualizace dat přes aplikaci",
        "content": encoded_content,
    }
    if sha:
      payload["sha"] = sha

    put_resp = requests.put(url, headers=headers, json=payload)
    if put_resp.status_code not in [200, 201]:
      st.error(f"Chyba při ukládání na GitHub: {put_resp.status_code}")
  else:
    with open(FILE_PATH, "w", encoding="utf-8") as f:
      json.dump(data_to_save, f, ensure_ascii=False, indent=4)


# Inicializace stavu
if "leagues" not in st.session_state:
  st.session_state.leagues = load_data(show_messages=False)

st.title("⚽🏒 SportStats - Správa lig")
st.markdown("Aplikace pro správu týmů, zápasů a střelců.")

# Postranní panel
st.sidebar.header("⚙️ Navigace")

# Tlačítko pro manuální načtení
if st.sidebar.button("🔄 Načíst aktuální data ze souboru"):
  st.session_state.leagues = load_data(show_messages=True)
  st.rerun()

with st.sidebar.expander("➕ Vytvořit novou ligu"):
  new_league_name = st.text_input("Název ligy")
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
        st.success(f"Liga '{league_clean}' byla vytvořena a uložena!")
        st.rerun()
      else:
        st.error("Tato liga již existuje!")
    else:
      st.error("Zadejte název ligy!")

league_name = st.sidebar.selectbox(
    "Vyberte ligu", list(st.session_state.leagues.keys())
)
current_league = st.session_state.leagues[league_name]

if st.sidebar.button("🔄 Resetovat vše do výchozího stavu"):
  if HAS_GITHUB:
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{FILE_PATH}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
    }
    get_resp = requests.get(url, headers=headers)
    if get_resp.status_code == 200:
      sha = get_resp.json().get("sha")
      requests.delete(
          url,
          headers=headers,
          json={"message": "Reset dat", "sha": sha},
      )
  elif os.path.exists(FILE_PATH):
    os.remove(FILE_PATH)
  del st.session_state.leagues
  st.rerun()

st.header(f"🏆 {league_name}")

# Hlavní záložky
tab1, tab2, tab3, tab4 = st.tabs(
    ["📊 Aktuální tabulka", "📅 Zápasy", "⚽ Střelci", "🛡️ Správa týmů"]
)

# 1. TABULKA
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

# 2. ZÁPASY
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
          st.success("Zápas byl zapsán!")
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

# 3. STŘELCI
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
          st.success("Střelec byl přidán!")
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
