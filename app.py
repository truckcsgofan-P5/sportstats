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


# Výchozí data (přidán ukázkový nadcházející zápas s "Odehráno": False)
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
              },  # Ukázka nadcházejícího zápasu
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


# Funkce pro načtení dat
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
        "message": "Aktualizace sportovních dat",
        "content": encoded_content,
    }
    if sha:
      payload["sha"] = sha

    requests.put(url, headers=headers, json=payload)
  else:
    with open(FILE_PATH, "w", encoding="utf-8") as f:
      json.dump(data_to_save, f, ensure_ascii=False, indent=4)


# Výpočet pravděpodobnosti výhry pro nadcházející zápas
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
      base *= 1.25  # Domácí zvýhodnění
    return base

  r_home = get_rating(home_team, is_home=True)
  r_away = get_rating(away_team, is_home=False)

  total = r_home + r_away
  home_share = r_home / total
  away_share = r_away / total

  p_draw = 0.25  # Pevný odhad pro remízu (~25%)
  p_home = (1 - p_draw) * home_share
  p_away = (1 - p_draw) * away_share

  return p_home * 100, p_draw * 100, p_away * 100


# Inicializace stavu
if "leagues" not in st.session_state:
  st.session_state.leagues = load_data()

st.title("⚽🏒 SportStats - Kompletní správa a statistiky")
st.markdown("Aplikace pro správu lig, týmů, zápasů, statistik a predikcí.")

# Postranní panel
st.sidebar.header("⚙️ Navigace")

if st.sidebar.button("🔄 Načíst aktuální data ze souboru"):
  st.session_state.leagues = load_data()
  st.success("Data byla úspěšně načtena!")
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
        st.success(f"Liga '{league_clean}' byla vytvořena!")
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
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Aktuální tabulka",
    "📅 Zápasy & Nadcházející",
    "⚽ Střelci",
    "🛡️ Správa týmů",
    "📈 Statistiky",
])

# 1. TABULKA
with tab1:
  st.subheader("Tabulka ligy")
  matches_df = current_league["matches"]
  teams_list = current_league["teams"]
  table_data = {}

  if not teams_list:
    st.info(
        "V této lize zatím nejsou žádné týmy. Přejděte do záložky '🛡️ Správa"
        " týmů' a přidejte je."
    )
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

# 2. ZÁPASY & NADCHÁZEJÍCÍ ZÁPASY S PREDIKCÍ
with tab2:
  st.subheader("📅 Správa zápasů a nadcházející duely")
  teams_list = current_league["teams"]

  if len(teams_list) >= 2:
    with st.form("add_match_form"):
      st.markdown("**Přidat nový zápas (nebo naplánovat nadcházející):**")
      col1, col2, col3, col4, col5 = st.columns([2.5, 1, 1, 2.5, 1.5])
      with col1:
        home_team = st.selectbox("Domácí tým", teams_list, index=0)
      with col2:
        home_score = st.number_input(
            "Góly dom.", min_value=0, value=0, step=1
        )
      with col3:
        away_score = st.number_input(
            "Góly hosté", min_value=0, value=0, step=1
        )
      with col4:
        default_away_idx = 1 if len(teams_list) > 1 else 0
        away_team = st.selectbox(
            "Hostující tým", teams_list, index=default_away_idx
        )
      with col5:
        is_played = st.checkbox("Odehráno", value=True)

      submitted = st.form_submit_button("➕ Přidat zápas")
      if submitted:
        if home_team == away_team:
          st.error("Domácí a hostující tým nemůže být stejný!")
        else:
          new_row = pd.DataFrame([{
              "Domácí": home_team,
              "Hosté": away_team,
              "Skóre Domácí": int(home_score),
              "Skóre Hosté": int(away_score),
              "Odehráno": bool(is_played),
          }])
          current_league["matches"] = pd.concat(
              [current_league["matches"], new_row], ignore_index=True
          )
          save_data()
          st.success("Zápas byl úspěšně přidán!")
          st.rerun()
  else:
    st.warning("Pro zápis zápasů musíte mít v lize zadané alespoň 2 týmy.")

  st.divider()

  # SEKCE: NADCHÁZEJÍCÍ ZÁPASY S PREDIKCÍ ŠANCÍ
  st.subheader("🔮 Nadcházející zápasy & šance na výhru")
  matches_df = current_league["matches"]

  if not matches_df.empty and "Odehráno" in matches_df.columns:
    upcoming_df = matches_df[matches_df["Odehráno"] == False]

    if not upcoming_df.empty:
      st.markdown(
          "Pravděpodobnosti jsou vypočteny na základě dosavadní formy týmů v"
          " lize a domácího prostředí."
      )
      for idx, row in upcoming_df.iterrows():
        h_team = row["Domácí"]
        a_team = row["Hosté"]

        p_home, p_draw, p_away = calculate_win_probabilities(
            h_team, a_team, matches_df, teams_list
        )

        with st.container(border=True):
          cols = st.columns([3, 2, 3])
          with cols[0]:
            st.markdown(f"### 🏠 **{h_team}**")
            st.metric("Šance na výhru", f"{p_home:.1f} %")
          with cols[1]:
            st.markdown(
                f"<div style='text-align: center; padding-top: 15px;'><b>VS</b><br><span"
                f" style='font-size: 13px; color: gray;'>Remíza: {p_draw:.1f}"
                f" %</span></div>",
                unsafe_allow_html=True,
            )
          with cols[2]:
            st.markdown(
                f"<div style='text-align: right;'><h3>✈️"
                f" <b>{a_team}</b></h3></div>",
                unsafe_allow_html=True,
            )
            st.markdown(
                f"<div style='text-align: right;'>Šance na výhru:"
                f" <b>{p_away:.1f} %</b></div>",
                unsafe_allow_html=True,
            )
    else:
      st.info(
          "Žádné nadcházející zápasy. V horním formuláři zrušte zaškrtnutí"
          " políčka 'Odehráno' a naplánujte nový zápas."
      )
  else:
    st.info("Zatím nejsou vytvořeny žádné zápasy.")

  st.divider()
  st.subheader("Seznam všech zápasů (možnost úpravy)")
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

# 5. STATISTIKY
with tab5:
  st.subheader("📈 Pokročilé statistiky týmů")
  teams_list = current_league["teams"]
  matches_df = current_league["matches"]

  if not teams_list:
    st.warning("V lize nejsou žádné týmy.")
  elif matches_df.empty:
    st.info("Zatím nejsou k dispozici žádné zápasy pro výpočet statistik.")
  else:
    st.markdown("### 📊 Detailní statistiky týmu")
    selected_team = st.selectbox("Vyberte tým pro zobrazení statistik", teams_list)

    home_matches = matches_df[
        (matches_df["Domácí"] == selected_team)
        & (matches_df.get("Odehráno", True) == True)
    ]
    away_matches = matches_df[
        (matches_df["Hosté"] == selected_team)
        & (matches_df.get("Odehráno", True) == True)
    ]

    h_played = len(home_matches)
    h_wins, h_draws, h_losses, h_gf, h_ga = 0, 0, 0, 0, 0
    for _, r in home_matches.iterrows():
      try:
        s_home = int(r["Skóre Domácí"])
        s_away = int(r["Skóre Hosté"])
        h_gf += s_home
        h_ga += s_away
        if s_home > s_away:
          h_wins += 1
        elif s_home < s_away:
          h_losses += 1
        else:
          h_draws += 1
      except:
        pass

    a_played = len(away_matches)
    a_wins, a_draws, a_losses, a_gf, a_ga = 0, 0, 0, 0, 0
    for _, r in away_matches.iterrows():
      try:
        s_home = int(r["Skóre Domácí"])
        s_away = int(r["Skóre Hosté"])
        a_gf += s_away
        a_ga += s_home
        if s_away > s_home:
          a_wins += 1
        elif s_away < s_home:
          a_losses += 1
        else:
          a_draws += 1
      except:
        pass

    tot_played = h_played + a_played
    tot_gf = h_gf + a_gf
    tot_ga = h_ga + a_ga

    col1, col2, col3 = st.columns(3)
    with col1:
      st.metric(
          "🏠 Doma (V - R - P)", f"{h_wins} - {h_draws} - {h_losses}", f"Zápasů: {h_played}"
      )
      st.markdown(
          f"Skóre doma: **{h_gf}:{h_ga}** (Průměr gólů na zápas: **{h_gf/h_played:.2f}**)"
          if h_played > 0
          else "Zatím bez domácích zápasů"
      )
    with col2:
      st.metric(
          "✈️ Venku (V - R - P)", f"{a_wins} - {a_draws} - {a_losses}", f"Zápasů: {a_played}"
      )
      st.markdown(
          f"Skóre venku: **{a_gf}:{a_ga}** (Průměr gólů na zápas: **{a_gf/a_played:.2f}**)"
          if a_played > 0
          else "Zatím bez venkovních zápasů"
      )
    with col3:
      st.metric(
          "⚽ Celkem gólů na zápas",
          f"{(tot_gf/tot_played):.2f}" if tot_played > 0 else "0",
          f"Vstřelené celkem: {tot_gf}",
      )
      st.markdown(
          f"Inkresované celkem: **{tot_ga}**"
          if tot_played > 0
          else ""
      )

    st.divider()

    st.markdown("### ⚔️ Vzájemný zápas & Odhad šancí (Head-to-Head)")
    col_t1, col_t2 = st.columns(2)
    with col_t1:
      team_a = st.selectbox("Tým A (Domácí/První)", teams_list, index=0)
    with col_t2:
      default_idx = 1 if len(teams_list) > 1 else 0
      team_b = st.selectbox("Tým B (Hosté/Druhý)", teams_list, index=default_idx)

    if team_a == team_b:
      st.warning("Vyberte dva různé týmy pro porovnání.")
    else:
      h2h_matches = matches_df[
          ((matches_df["Domácí"] == team_a) & (matches_df["Hosté"] == team_b))
          | ((matches_df["Domácí"] == team_b) & (matches_df["Hosté"] == team_a))
      ]
      h2h_played_df = h2h_matches[h2h_matches.get("Odehráno", True) == True]

      h2h_played = len(h2h_played_df)
      t1_wins = 0
      t2_wins = 0
      draws = 0
      t1_goals = 0
      t2_goals = 0

      h2h_list = []
      for _, r in h2h_matches.iterrows():
        try:
          hs = int(r["Skóre Domácí"])
          as_ = int(r["Skóre Hosté"])
          home = r["Domácí"]
          away = r["Hosté"]
          is_played_match = r.get("Odehráno", True)

          if is_played_match:
            if home == team_a:
              t1_goals += hs
              t2_goals += as_
              if hs > as_:
                t1_wins += 1
              elif hs < as_:
                t2_wins += 1
              else:
                draws += 1
            else:
              t1_goals += as_
              t2_goals += hs
              if as_ > hs:
                t1_wins += 1
              elif as_ < hs:
                t2_wins += 1
              else:
                draws += 1

          h2h_list.append({
              "Zápas": f"{home} {hs} : {as_} {away}",
              "Odehráno": is_played_match,
          })
        except:
          pass

      st.markdown(f"#### Vzájemná bilance: **{team_a}** vs **{team_b}**")
      c1, c2, c3, c4 = st.columns(4)
      c1.metric("Počet odehraných vzájemných zápasů", h2h_played)
      c2.metric(f"Výhry ({team_a})", t1_wins)
      c3.metric(f"Remízy", draws)
      c4.metric(f"Výhry ({team_b})", t2_wins)

      if h2h_played > 0:
        st.markdown(
            f"Vzájemné skóre gólů: **{team_a} {t1_goals} : {t2_goals} {team_b}**"
        )
        t1_chance = (t1_wins / h2h_played) * 100
        t2_chance = (t2_wins / h2h_played) * 100
        draw_chance = (draws / h2h_played) * 100
        st.markdown(
            f"📈 **Historická úspěšnost:** {team_a}: **{t1_chance:.1f}%** | Remíza:"
            f" **{draw_chance:.1f}%** | {team_b}: **{t2_chance:.1f}%**"
        )

        st.markdown("**Seznam vzájemných zápasů:**")
        for m in h2h_list:
          status = " (Odehráno)" if m["Odehráno"] else " (Nadcházející)"
          st.write(f"- {m['Zápas']}{status}")
      else:
        st.info(
            f"Týmy {team_a} a {team_b} spolu v této lize ještě nemají odehraný"
            " zápas."
        )
