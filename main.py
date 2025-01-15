import streamlit as st
import pandas as pd
import json
import os
import re
from datetime import datetime
import plotly.express as px
from collections import Counter

TEAM_PLAYERS = [
    "",
    "Peche le coquin",
    "ManGros Fish",
    "gumaguccy",
    "Cheikh Sadri"
]

def parse_date_from_filename(filename):
    """
    Extrait la date depuis un nom de fichier au format 'DD_MM_YYYY_G1.json'
    Retourne un objet datetime ou None si pas valide.
    """
    pattern = r'^(\d{2})_(\d{2})_(\d{4})_G\d+\.json$'
    match = re.match(pattern, filename)
    if not match:
        return None
    day   = int(match.group(1))
    month = int(match.group(2))
    year  = int(match.group(3))
    return datetime(year, month, day)

def main():
    st.title("Statistiques de l'équipe")

    # Sélection d'une date
    default_date = datetime.now().date()
    start_date = st.date_input(
        "Sélectionnez la date de départ (inclus)",
        value=default_date
    )

    # Sélection du nombre de parties
    x_matches = st.number_input(
        "Nombre de parties à analyser (les X dernières après la date)",
        min_value=1,
        max_value=50,
        value=5
    )

    # Dossier où se situent nos JSON
    json_folder = "scrims_json"

    if not os.path.exists(json_folder):
        st.error(f"Le dossier '{json_folder}' n'existe pas.")
        return
    
    # On parcourt tous les fichiers JSON pour récupérer (file_date, filename)
    all_files = [f for f in os.listdir(json_folder) if f.endswith(".json")]
    date_files = []
    for fname in all_files:
        file_date = parse_date_from_filename(fname)
        if file_date is None:
            continue  # fichier qui ne correspond pas au format
        date_files.append((file_date, fname))
    
    if not date_files:
        st.warning("Aucun fichier JSON avec un format valide trouvé.")
        return

    # Filtrer par date >= start_date
    date_files_filtered = [(d, f) for (d, f) in date_files if d.date() >= start_date]
    if not date_files_filtered:
        st.warning("Aucun match trouvé après cette date.")
        return
    
    # Trier par date croissante et prendre les X derniers
    date_files_filtered.sort(key=lambda x: x[0])
    if len(date_files_filtered) > x_matches:
        date_files_filtered = date_files_filtered[-x_matches:]

    st.write(f"**Matches retenus** : {len(date_files_filtered)}")
    st.write([f"{f} (Date: {d.strftime('%d/%m/%Y')})" for (d, f) in date_files_filtered])

    # -------------------------------------------------------
    # Variables pour cumuler les stats totales
    # -------------------------------------------------------
    nb_matches_parsed = 0

    # Objectifs / kills/morts (team) => accumulés
    total_grubs   = 0
    total_drakes  = 0
    total_barons  = 0
    total_herald  = 0
    total_towers  = 0

    total_team_kills  = 0
    total_team_deaths = 0

    # Stats par joueur => kills, deaths, assists, gold, damage, nbGames
    data_players = {
        name: {
            "Kills": 0,
            "Deaths": 0,
            "Assists": 0,
            "Gold": 0,
            "Damage": 0,
            "NbGames": 0
        }
        for name in TEAM_PLAYERS
    }

    # -------------------------------------------------------
    # Parcours des matches filtrés
    # -------------------------------------------------------
    for d, fname in date_files_filtered:
        path = os.path.join(json_folder, fname)
        with open(path, "r", encoding="utf-8") as f:
            match_data = json.load(f)
        participants = match_data.get("participants", [])
        if not participants:
            continue

        # 1) Identifier la TEAM ("100" ou "200") où se trouvent
        #    nos joueurs. On récupère un max de noms (TEAM) parmi nos 5
        #    participants => On prend la majorité
        team_candidates = []
        for p in participants:
            player_name = p.get("NAME", "")
            if player_name in TEAM_PLAYERS:
                # => On retient la TEAM
                team_candidates.append(p.get("TEAM"))  # ex "100" ou "200"

        if not team_candidates:
            # Pas de nos joueurs => on skip
            continue

        c = Counter(team_candidates)
        my_team = c.most_common(1)[0][0]  # "100" ou "200"

        # 2) Cumuler les stats d'équipe (objectifs / kills / deaths / grubs)
        match_team_kills  = 0
        match_team_deaths = 0
        match_team_drakes = 0
        match_team_barons = 0
        match_team_herald = 0
        match_team_towers = 0
        match_team_grubs  = 0

        for p in participants:
            if p.get("TEAM") == my_team:
                match_team_kills  += int(p.get("CHAMPIONS_KILLED", 0))
                match_team_deaths += int(p.get("NUM_DEATHS", 0))
                match_team_drakes += int(p.get("DRAGON_KILLS", 0))
                match_team_barons += int(p.get("BARON_KILLS", 0))
                match_team_herald += int(p.get("RIFT_HERALD_KILLS", 0))
                match_team_towers += int(p.get("TURRET_TAKEDOWNS", 0))
                match_team_grubs  += int(p.get("HORDE_KILLS", 0))

        total_team_kills  += match_team_kills
        total_team_deaths += match_team_deaths
        total_drakes      += match_team_drakes
        total_barons      += match_team_barons
        total_herald      += match_team_herald
        total_towers      += match_team_towers
        total_grubs       += match_team_grubs

        # 3) Stats par joueur (si NAME in TEAM_PLAYERS)
        #    Kills, Deaths, Assists, Gold, Damage, +1 game
        for p in participants:
            name = p.get("NAME", "")
            if name in data_players:
                data_players[name]["Kills"]   += int(p.get("CHAMPIONS_KILLED", 0))
                data_players[name]["Deaths"]  += int(p.get("NUM_DEATHS", 0))
                data_players[name]["Assists"] += int(p.get("ASSISTS", 0))
                data_players[name]["Gold"]    += int(p.get("GOLD_EARNED", 0))
                data_players[name]["Damage"]  += int(p.get("TOTAL_DAMAGE_DEALT_TO_CHAMPIONS", 0))
                data_players[name]["NbGames"] += 1

        nb_matches_parsed += 1

    if nb_matches_parsed == 0:
        st.warning("Aucune partie trouvée avec nos joueurs dans la sélection.")
        return

    st.write(f"**Nombre de parties effectivement parsées** : {nb_matches_parsed}")

    # -------------------------------------------------------
    # Calculs de moyennes sur nb_matches_parsed
    # -------------------------------------------------------
    # Grubs moyen
    avg_grubs = total_grubs / nb_matches_parsed
    # kills/morts totaux moyens
    avg_team_kills  = total_team_kills  / nb_matches_parsed
    avg_team_deaths = total_team_deaths / nb_matches_parsed
    # objectifs moyens
    avg_drakes = total_drakes / nb_matches_parsed
    avg_barons = total_barons / nb_matches_parsed
    avg_herald = total_herald / nb_matches_parsed
    avg_towers = total_towers / nb_matches_parsed

    team_stats_df = pd.DataFrame([{
        "Moy. Grubs":       round(avg_grubs,2),
        "Moy. KillsTeam":   round(avg_team_kills,2),
        "Moy. DeathsTeam":  round(avg_team_deaths,2),
        "Moy. Drakes":      round(avg_drakes,2),
        "Moy. Nashors":     round(avg_barons,2),
        "Moy. Heralds":     round(avg_herald,2),
        "Moy. Towers":      round(avg_towers,2)
    }])

    st.subheader("Statistiques moyennes (équipe)")
    st.dataframe(team_stats_df, hide_index=True)

    # -------------------------------------------------------
    # Stats par joueur => moyenne
    # -------------------------------------------------------
    player_rows = []
    for name, stats in data_players.items():
        nb = stats["NbGames"]
        if nb == 0:
            continue

        # Remplacer le nom par le pseudo correspondant
        if name == "":
            displayed_name = "Nireo"
        elif name == "Peche le coquin":
            displayed_name = "Peche"
        elif name == "ManGros Fish":
            displayed_name = "Jawa"
        elif name == "gumaguccy":
            displayed_name = "kross"
        elif name == "Cheikh Sadri":
            displayed_name = "iench taric"
        else:
            displayed_name = name  # fallback si jamais on en ajoute d'autres un jour

        avg_kills   = stats["Kills"]   / nb
        avg_deaths  = stats["Deaths"]  / nb
        avg_assists = stats["Assists"] / nb
        avg_gold    = stats["Gold"]    / nb
        avg_damage  = stats["Damage"]  / nb

        # Kill Participation => (Sum of (Kills+Assists)) / total_team_kills (global)
        # On l'affiche en pourcentage
        if total_team_kills > 0:
            kp = round((stats["Kills"] + stats["Assists"]) / total_team_kills * 100, 1)
        else:
            kp = 0.0

        player_rows.append({
            "Joueur": displayed_name,
            "NbGames": nb,
            "AvgKills": round(avg_kills,1),
            "AvgDeaths": round(avg_deaths,1),
            "AvgAssists": round(avg_assists,1),
            "AvgGold": round(avg_gold,1),
            "AvgDamage": round(avg_damage,1),
            "KillParticipation(%)": kp
        })

    player_df = pd.DataFrame(player_rows)
    st.subheader("Moyennes par joueur")
    st.dataframe(player_df, hide_index=True)

    # -------------------------------------------------------
    # Graphique : Dégâts vs Gold (moyenne)
    # -------------------------------------------------------
    if not player_df.empty:
        fig = px.scatter(
            player_df,
            x="AvgGold",
            y="AvgDamage",
            color="Joueur",
            text="Joueur",
            title="Dégâts en fonction des Golds (moyenne par joueur)"
        )
        fig.update_traces(textposition='top center')
        st.plotly_chart(fig)
    else:
        st.write("Aucun joueur trouvé pour le graphique.")

if __name__ == "__main__":
    main()
