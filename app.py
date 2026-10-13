import pandas as pd
import streamlit as st

# Nastavení stránky
st.set_page_config(
    page_title="SportStats - Aplikace", page_icon="⚽", layout="wide"
)

st.title("⚽🏒 SportStats - Správa lig a výsledků")
st.markdown(
    "Tato aplikace slouží pro pohodlnou správu zápasů, střelců a automatický"
    " výpočet tabulek."
)

# Výchozí data v paměti aplikace
if "leagues" not in st.session_state:
  st.session_state.leagues = {
      "Premier League (Anglie)": {
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
                  "Skóre Domácí": 1,
                  "Skóre Hosté": 0,
                  "Odehráno": True,
              },
          ]),
          "scorers": pd.DataFrame([
              {"Hráč": "Erling Haaland", "Tým": "Manchester City", "Góly": 10},
              {"Hráč": "Cole Palmer", "Tým": "Chelsea", "Góly": 7},
          ]),
      },
      "La Liga (Španělsko)": {
          "matches": pd.DataFrame([
              {
                  "Domácí": "Real Madrid",
                  "Hosté": "Barcelona",
                  "Skóre Domácí": 2,
                  "Skóre Hosté": 1,
                  "Odehráno": True,
              },
              {
                  "Domácí": "Atletico Madrid",
                  "Hosté": "Villarreal",
                  "Skóre Domácí": 3,
                  "Skóre Hosté": 0,
                  "Odehráno": True,
              },
          ]),
          "scorers": pd.DataFrame([
              {"Hráč": "Kylian Mbappé", "Tým": "Real Madrid", "Góly": 9},
              {"Hráč": "Robert Lewandowski", "Tým": "Barcelona", "Góly": 8},
          ]),
      },
  }

# Postranní panel pro výběr ligy
st.sidebar.header("⚙️ Navigace")
league_name = st.sidebar.selectbox(
    "Vyberte ligu", list(st.session_state.leagues.keys())
)
current_league = st.session_state.leagues[league_name]

# Tlačítko pro reset dat (pokud by se tabulka rozbila)
if st.sidebar.button("🔄 Resetovat data ligy"):
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

  # Bezpečnostní kontrola sloupců
  required_cols = {"Domácí", "Hosté", "Skóre Domácí", "Skóre Hosté"}
  if not required_cols.issubset(matches_df.columns):
    st.error(
        "⚠️ V tabulce zápasů došlo ke změně názvů sloupců! Použijte prosím"
        " tlačítko 'Resetovat data ligy' v postranním panelu."
    )
  else:
    for _, row in matches_df.iterrows():
      if row.get("Odehráno", True):
        home = row["Domácí"]
        away = row["Hosté"]
        try:
          hs = int(row["Skóre Domácí"])
          as_ = int(row["Skóre Hosté"])
        except (ValueError, TypeError):
          continue  # Přeskočí neplatné hodnoty

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

    if table_data:
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
        })
      standings_df = pd.DataFrame(standings_list).sort_values(
          by=["Body", "GD", "Vstřelené"], ascending=False
      )
      standings_df.reset_index(drop=True, inplace=True)
      standings_df.index += 1
      st.dataframe(standings_df, use_container_width=True)
    else:
      st.info("Zatím nejsou k dispozici žádné platné odehrané zápasy.")

# 2. SPRÁVA ZÁPASŮ
with tab2:
  st.subheader("Správa zápasů a výsledků")
  st.markdown(
      "Zde můžete přímo v tabulce přepisovat výsledky nebo přidávat nové zápasy"
      " (kliknutím na + nebo na konec tabulky)."
  )

  edited_matches = st.data_editor(
      current_league["matches"],
      num_rows="dynamic",
      key=f"matches_editor_{league_name}",
      use_container_width=True,
  )
  current_league["matches"] = edited_matches

# 3. SPRÁVA STŘELCŮ
with tab3:
  st.subheader("Top střelci")
  st.markdown(
      "Upravujte góly hráčů přímo v tabulce. Můžete také přidávat nové řádky."
  )

  edited_scorers = st.data_editor(
      current_league["scorers"],
      num_rows="dynamic",
      key=f"scorers_editor_{league_name}",
      use_container_width=True,
  )
  current_league["scorers"] = edited_scorers
