import base64
import json
import os
import pandas as pd
import requests
import streamlit as st

st.set_page_config(
    page_title="SportStats - Aplikace", page_icon="⚽", layout="wide"
)

HAS_GITHUB = "GITHUB_TOKEN" in st.secrets and "GITHUB_REPO" in st.secrets
GITHUB_TOKEN = st.secrets.get("GITHUB_TOKEN", "")
GITHUB_REPO = st.secrets.get("GITHUB_REPO", "")
FILE_PATH = "sports_data.json"


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
              {
                  "Domácí": "Manchester United",
                  "Hosté": "Tottenham",
                  "Skóre Domácí": 0,
                  "Skóre Hosté": 0,
                  "Odehráno": False,
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
              },
              {
                  "Domácí": "Barcelona",
                  "Hosté": "Atletico Madrid",
                  "Skóre Domácí": 0,
                  "Skóre Hosté": 0,
                  "Odehráno": False,
              },
          ]),
          "scorers": pd.DataFrame([
              {"Hráč": "Kylian Mbappé", "Tým": "Real Madrid", "Góly": 9},
              {"Hráč": "Robert Lewandowski", "Tým": "Barcelona", "Góly": 8},
          ]),
      },
  }


def load_data():
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
        return loaded
    except Exception:
      pass
  else:
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
        return loaded
      except Exception:
        pass

  return get_default_data()


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
        "message": "Aktualizace sportovních dat",
        "content": encoded_content,
    }
    if sha:
      payload["sha"] = sha

    requests.put(url, headers=headers, json=payload)
  else:
    with open(FILE_PATH, "w", encoding="utf-8") as f:
      json.dump(data_to_save, f, ensure_ascii=False, indent=4)


def calculate_win_probabilities(home_team, away_team, matches_df, teams_list):
  played_df = matches_df[matches_df.get("Odehráno", True) == True]
  team_stats = {t: {"points": 0, "played": 0, "gd": 0} for t in teams_list}

  for _, r in played_df.iterrows():
    try:
      h = r["Domácí"]
      a = r["Hosté"]
      hs = int(r["Skóre Domácí"])
      as_ = int(r["Skóre Hosté"])
      if h in team_stats:
        team_stats[h]["played"] += 1
        team_stats[h]["gd"] += hs - as_
        if hs > as_:
          team_stats[h]["points"] += 3
        elif hs == as_:
          team_stats[h]["points"] += 1
      if a in team_stats:
        team_stats[a]["played"] += 1
        team_stats[a]["gd"] += as_ - hs
        if as_ > hs:
          team_stats[a]["points"] += 3
        elif as_ == hs:
          team_stats[a]["points"] += 1
    except:
      pass

  def get_rating(t, is_home=False):
    st_data = team_stats.get(t, {"points": 0, "played": 0, "gd": 0})
    if st_data["played"] == 0:
      base = 1.0
    else:
      ppg = st_data["points"] / st_data["played"]
      gd_per_g = st_data["gd"] / st_data["played"]
      base = max(0.2, ppg * 0.7 + gd_per_g * 0.3 + 1.0)
    if is_home:
      base *= 1.25
    return base

  r_home = get_rating(home_team, is_home=True)
  r_away = get_rating(away_team, is_home=False)

  total = r_home + r_away
  home_share = r_home / total
  away_share = r_away / total

  p_draw = 0.25
  p_home = (1 - p_draw) * home_share
  p_away = (1 - p_draw) * away_share

  return p_home * 100, p_draw * 100, p_away * 100


if "leagues" not in st.session_state:
  st.session_state.leagues = load_data()

st.title("⚽🏒 SportStats")
st.markdown("Správa lig, zápasů a statistik.")

st.sidebar.header("⚙️ Navigace")

if st.sidebar.button("🔄 Načíst data ze souboru"):
  st.session_state.leagues = load_data()
  st.success("Data byla načtena!")
  st.rerun()

with st.sidebar.expander("➕ Vytvořit ligu"):
  new_league_name = st.text_input("Název ligy")
  if st.button("Vytvořit"):
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
        st.success(f"Liga '{league_clean}' vytvořena!")
        st.rerun()
      else:
        st.error("Liga již existuje!")
    else:
      st.error("Zadejte název!")

league_name = st.sidebar.selectbox(
    "Vyberte ligu", list(st.session_state.leagues.keys())
)
current_league = st.session_state.leagues[league_name]

if st.sidebar.button("🔄 Resetovat data"):
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

tab1, tab2, tab3, tab4, tab5 = st.tabs(
    ["📊 Tabulka", "📅 Zápasy", "⚽ Střelci", "🛡️ Týmy", "📈 Statistiky"]
)

with tab1:
  st.subheader("Tabulka ligy")
  matches_df = current_league["matches"]
  teams_list = current_league["teams"]
  table_data = {}

  if not teams_list:
    st.info("V lize nejsou žádné týmy. Přidejte je v záložce '🛡️ Týmy'.")
  else:
    for team in teams_list:
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

    if standings_list:
      standings_df = pd.DataFrame(standings_list).sort_values(
          by=["Body", "GD", "Vstřelené"], ascending=False
      )
      standings_df = standings_df.drop(columns=["Vstřelené"])
      standings_df.reset_index(drop=True, inplace=True)
      standings_df.index += 1
      st.dataframe(standings_df, use_container_width=True)

with tab2:
  st.subheader("📅 Zápasy & Predikce")
  teams_list = current_league["teams"]

  if len(teams_list) >= 2:
    with st.form("add_match_form"):
      st.markdown("**Nový zápas:**")
      col1, col2, col3 = st.columns([3, 2, 3])
      with col1:
        home_team = st.selectbox("Domácí", teams_list, index=0)
        home_score = st.number_input("Góly dom.", min_value=0, value=0, step=1)
      with col2:
        default_away_idx = 1 if len(teams_list) > 1 else 0
        away_team = st.selectbox("Hosté", teams_list, index=default_away_idx)
        away_score = st.number_input("Góly hosté", min_value=0, value=0, step=1)
      with col3:
        is_played = st.checkbox("Odehráno", value=True)
        submitted = st.form_submit_button("➕ Přidat")

      if submitted:
        if home_team == away_team:
          st.error("Týmy musí být jiné!")
        else:
          new_row = pd.DataFrame([{
              "Domácí": home_team,
              "Hosté": away_team,
              "Skóre Domácí": int(home_score),
              "Skóre Hosté": int(away_score),
              "Odehráno": bool(is_played),
          }])
          current_league["matches"] = pd.
