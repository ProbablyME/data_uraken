import streamlit as st
st.set_page_config(layout="wide")

import pandas as pd
import json
import os
import re
from datetime import datetime
from collections import Counter, defaultdict
import requests
from PIL import Image
from io import BytesIO

# Liste des joueurs de l'équipe URAKEN
TEAM_PLAYERS = [
    "",
    "Peche le coquin",
    "ManGros Fish",
    "gumaguccy",
    "Cheikh Sadri"
]

# Conversion des positions d'équipe en rôles standard
ROLE_MAPPING = {
    "TOP": "TOP",
    "JUNGLE": "JUNGLE",
    "MIDDLE": "MIDDLE",
    "MID": "MIDDLE",      # Au cas où 'MID' apparaisse
    "BOTTOM": "BOTTOM",
    "BOT": "BOTTOM",      # Au cas où 'BOT' apparaisse
    "UTILITY": "UTILITY",
    "SUPPORT": "UTILITY"  # Au cas où 'SUPPORT' apparaisse
}

def parse_date_from_filename(filename):
    """
    Extrait la date depuis un nom de fichier au format 'DD_MM_YYYY_GX.json'
    Retourne un objet datetime ou None si le nom ne correspond pas.
    """
    pattern = r'^(\d{2})_(\d{2})_(\d{4})_G\d+\.json$'
    match = re.match(pattern, filename)
    if not match:
        return None
    day   = int(match.group(1))
    month = int(match.group(2))
    year  = int(match.group(3))
    return datetime(year, month, day)

def get_champion_icon_url(champion_name):
    """
    Retourne l'URL de l'icône pour le champion donné (ex: 'Renekton').
    """
    ddragon_version = "14.2.1"  # À mettre à jour quand nécessaire
    # Remplacer les espaces et les apostrophes par des tirets si nécessaire
    # DDragon utilise des noms de champions sans espaces et avec une capitalisation correcte
    formatted_name = champion_name.replace(" ", "").replace("'", "").capitalize()
    return f"https://ddragon.leagueoflegends.com/cdn/{ddragon_version}/img/champion/{formatted_name}.png"

def display_champion_stats(champion_data):
    """
    Affiche dans l'onglet "Champions" les champions joués par chaque joueur,
    leur icône, le nombre de games et le taux de victoire (win rate).
    """
    st.subheader("Statistiques des champions par joueur")
    
    cols = st.columns(len(TEAM_PLAYERS))
    
    for idx, player in enumerate(TEAM_PLAYERS):
        displayed_name = {
            "": "Nireo",
            "Peche le coquin": "Peche",
            "ManGros Fish": "Jawa",
            "gumaguccy": "kross",
            "Cheikh Sadri": "iench taric"
        }.get(player, player)
        
        with cols[idx]:
            st.write(f"**{displayed_name}**")
            
            if player in champion_data:
                # On trie les champions par nombre de parties jouées puis par winrate
                champs = sorted(
                    champion_data[player].items(),
                    key=lambda x: (
                        x[1]['games'],
                        (x[1]['wins'] / x[1]['games']) if x[1]['games'] > 0 else 0
                    ),
                    reverse=True
                )
                
                for champ_name, stats in champs:
                    with st.container():
                        # Affichage de l'icône du champion
                        try:
                            icon_url = get_champion_icon_url(champ_name)
                            response = requests.get(icon_url)
                            img = Image.open(BytesIO(response.content))
                            st.image(img, width=40)
                        except:
                            st.write(f"*{champ_name}* (Icône indisponible)")
                        
                        # Calcul du winrate
                        winrate = 0
                        if stats['games'] > 0:
                            winrate = (stats['wins'] / stats['games']) * 100
                        
                        st.write(f"**{champ_name}**")
                        st.write(f"Games: {stats['games']}")
                        st.write(f"Winrate: {winrate:.1f}%")
                        st.write("---")
            else:
                st.write("Pas de données")

def main():
    st.title("Statistiques URAKEN")

    # Onglets
    tab1, tab2 = st.tabs(["Statistiques générales", "Champions"])
    
    with tab1:
        # 1) Paramètres
        default_date = datetime.now().date()
        start_date = st.date_input(
            "Sélectionnez la date de départ (inclus)",
            value=default_date
        )
        x_matches = st.number_input(
            "Nombre de parties à analyser (les X dernières après la date)",
            min_value=1,
            max_value=50,
            value=5
        )

        # 2) Dossier JSON
        json_folder = "scrims_json"
        if not os.path.exists(json_folder):
            st.error(f"Le dossier '{json_folder}' n'existe pas.")
            return
        
        # 3) Lister fichiers JSON + parse date
        all_files = [f for f in os.listdir(json_folder) if f.endswith(".json")]
        date_files = []
        for fname in all_files:
            file_date = parse_date_from_filename(fname)
            if file_date is None:
                continue
            date_files.append((file_date, fname))

        if not date_files:
            st.warning("Aucun fichier JSON au format attendu trouvé.")
            return

        # 4) Filtrer par date >= start_date
        date_files_filtered = [(d, f) for (d, f) in date_files if d.date() >= start_date]
        if not date_files_filtered:
            st.warning("Aucun match trouvé après cette date.")
            return
        
        # 5) Trier + prendre les X derniers
        date_files_filtered.sort(key=lambda x: x[0])
        if len(date_files_filtered) > x_matches:
            date_files_filtered = date_files_filtered[-x_matches:]

        st.write(f"**Matches retenus** : {len(date_files_filtered)}")
        st.write([f"{f} (Date: {d.strftime('%d/%m/%Y')})" for (d, f) in date_files_filtered])

        if not date_files_filtered:
            st.warning("Aucun fichier à traiter.")
            return

        # -------------------------------------------------------
        # Stats d'équipe (objectifs, kills, etc.)
        # -------------------------------------------------------
        nb_matches_parsed = 0
        total_wins = 0

        total_drakes  = 0
        total_barons  = 0
        total_herald  = 0
        total_towers  = 0
        total_grubs   = 0

        total_team_kills  = 0
        total_team_deaths = 0

        # -------------------------------------------------------
        # Stats par joueur
        # -------------------------------------------------------
        data_players = {
            name: {
                "Kills":   0,
                "Deaths":  0,
                "Assists": 0,
                "Gold":    0,
                "Damage":  0,
                "NbGames": 0,
                "KP":      0  # Kill Participation
            }
            for name in TEAM_PLAYERS
        }

        # -------------------------------------------------------
        # Stats par rôle
        # -------------------------------------------------------
        data_roles = {
            "TOP":     {"Gold": 0, "Damage": 0},
            "JUNGLE":  {"Gold": 0, "Damage": 0},
            "MIDDLE":  {"Gold": 0, "Damage": 0},
            "BOTTOM":  {"Gold": 0, "Damage": 0},
            "UTILITY": {"Gold": 0, "Damage": 0},
        }

        data_roles_games_count = {
            "TOP": 0,
            "JUNGLE": 0,
            "MIDDLE": 0,
            "BOTTOM": 0,
            "UTILITY": 0
        }

        # -------------------------------------------------------
        # Stats de champions : { player_name : { champ_name : {games, wins} } }
        # -------------------------------------------------------
        champion_stats = defaultdict(lambda: defaultdict(lambda: {'games': 0, 'wins': 0}))

        # -------------------------------------------------------
        # Parcours des matchs
        # -------------------------------------------------------
        for d, fname in date_files_filtered:
            path = os.path.join(json_folder, fname)
            with open(path, "r", encoding="utf-8") as f:
                match_data = json.load(f)

            participants = match_data.get("participants", [])
            if not participants:
                continue

            # Identifier la team "100" ou "200" de nos joueurs
            team_candidates = []
            for p in participants:
                player_name = p.get("NAME", "")
                if player_name in TEAM_PLAYERS:
                    team_candidates.append(p.get("TEAM"))

            if not team_candidates:
                continue

            c = Counter(team_candidates)
            # La team majoritaire (au cas où un bug) = "my_team"
            my_team = c.most_common(1)[0][0]  # ex: "100" ou "200"

            # Vérifier si la team a gagné
            # (on regarde un participant dans my_team qui a "WIN" = "Win")
            team_win = any(
                p.get("TEAM") == my_team and p.get("WIN", "").lower() == "win"
                for p in participants
            )
            if team_win:
                total_wins += 1

            match_team_kills  = 0
            match_team_deaths = 0
            match_team_drakes = 0
            match_team_barons = 0
            match_team_herald = 0
            match_team_towers = 0
            match_team_grubs  = 0

            # Stats d'équipe (objectifs, kills, etc.)
            for p in participants:
                if p.get("TEAM") == my_team:
                    kills  = int(p.get("CHAMPIONS_KILLED", 0))
                    deaths = int(p.get("NUM_DEATHS", 0))
                    drakes = int(p.get("DRAGON_KILLS", 0))
                    barons = int(p.get("BARON_KILLS", 0))
                    herald = int(p.get("RIFT_HERALD_KILLS", 0))
                    towers = int(p.get("TURRET_TAKEDOWNS", 0))
                    grubs  = int(p.get("HORDE_KILLS", 0))

                    match_team_kills  += kills
                    match_team_deaths += deaths
                    match_team_drakes += drakes
                    match_team_barons += barons
                    match_team_herald += herald
                    match_team_towers += towers
                    match_team_grubs  += grubs

            total_team_kills  += match_team_kills
            total_team_deaths += match_team_deaths
            total_drakes      += match_team_drakes
            total_barons      += match_team_barons
            total_herald      += match_team_herald
            total_towers      += match_team_towers
            total_grubs       += match_team_grubs

            # Stats par joueur + Stats par rôle + Stats de champion
            for p in participants:
                name = p.get("NAME", "")
                if name not in data_players:
                    # Pas un de nos joueurs => on ignore
                    continue

                kills    = int(p.get("CHAMPIONS_KILLED", 0))
                deaths   = int(p.get("NUM_DEATHS", 0))
                assists  = int(p.get("ASSISTS", 0))
                gold_str = p.get("GOLD_EARNED", "0")
                dmg_str  = p.get("TOTAL_DAMAGE_DEALT_TO_CHAMPIONS", "0")

                gold_val = int(gold_str) if gold_str.isdigit() else 0
                dmg_val  = int(dmg_str)  if dmg_str.isdigit()  else 0

                # Récupérer le nom du champion depuis le champ "SKIN"
                champ_name = p.get("SKIN", "Unknown")
                if champ_name == "Unknown":
                    st.warning(f"Le joueur {name} n'a pas de champion défini.")
                    continue

                # Incrémenter le compteur de games + victoires (si p.get("WIN") == "Win")
                champion_stats[name][champ_name]['games'] += 1
                if p.get("WIN", "").lower() == "win":
                    champion_stats[name][champ_name]['wins'] += 1

                # Kill Participation
                if match_team_kills > 0:
                    kp = (kills + assists) / match_team_kills * 100
                else:
                    kp = 0

                # Mise à jour des stats player
                data_players[name]["Kills"]   += kills
                data_players[name]["Deaths"]  += deaths
                data_players[name]["Assists"] += assists
                data_players[name]["Gold"]    += gold_val
                data_players[name]["Damage"]  += dmg_val
                data_players[name]["NbGames"] += 1
                data_players[name]["KP"]      += kp

                # Rôle
                role_raw = p.get("TEAM_POSITION", "") or p.get("INDIVIDUAL_POSITION", "")
                role_up  = role_raw.upper()
                role_std = ROLE_MAPPING.get(role_up, None)
                if role_std and role_std in data_roles:
                    data_roles[role_std]["Gold"]   += gold_val
                    data_roles[role_std]["Damage"] += dmg_val
                    data_roles_games_count[role_std] += 1

            nb_matches_parsed += 1

        if nb_matches_parsed == 0:
            st.warning("Aucune partie trouvée avec nos joueurs après filtrage.")
            return

        st.write(f"**Nombre de parties parsées** : {nb_matches_parsed}")

        # -------------------------------------------------------
        # Stats d'équipe => Moyennes
        # -------------------------------------------------------
        win_rate = (total_wins / nb_matches_parsed) * 100 if nb_matches_parsed > 0 else 0
        avg_drakes  = total_drakes      / nb_matches_parsed
        avg_barons  = total_barons      / nb_matches_parsed
        avg_herald  = total_herald      / nb_matches_parsed
        avg_towers  = total_towers      / nb_matches_parsed
        avg_grubs   = total_grubs       / nb_matches_parsed
        avg_kills   = total_team_kills  / nb_matches_parsed
        avg_deaths  = total_team_deaths / nb_matches_parsed

        team_stats_df = pd.DataFrame([{
            "Win Rate (%)":     round(win_rate,1),
            "Moy. Drakes":      round(avg_drakes,2),
            "Moy. Nashors":     round(avg_barons,2),
            "Moy. Heralds":     round(avg_herald,2),
            "Moy. Towers":      round(avg_towers,2),
            "Moy. Grubs":       round(avg_grubs,2),
            "Moy. KillsTeam":   round(avg_kills,2),
            "Moy. DeathsTeam":  round(avg_deaths,2),
        }])
        st.subheader("Statistiques moyennes (équipe)")
        st.dataframe(team_stats_df, hide_index=True)

        # -------------------------------------------------------
        # Stats par joueur => Moyennes
        # -------------------------------------------------------
        player_rows = []
        for name, stats in data_players.items():
            nb = stats["NbGames"]
            if nb == 0:
                continue

            # Renommage pour l'affichage
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
                displayed_name = name

            avg_kills   = stats["Kills"]   / nb
            avg_deaths  = stats["Deaths"]  / nb
            avg_assists = stats["Assists"] / nb
            avg_gold    = stats["Gold"]    / nb
            avg_dmg     = stats["Damage"]  / nb
            avg_kp      = stats["KP"]      / nb  # Kill Participation moyen

            # Gold Efficiency
            gold_eff = (avg_dmg / avg_gold) * 100 if avg_gold > 0 else 0

            player_rows.append({
                "Joueur":     displayed_name,
                "NbGames":    nb,
                "AvgKills":   round(avg_kills,1),
                "AvgDeaths":  round(avg_deaths,1),
                "AvgAssists": round(avg_assists,1),
                "KP(%)":      round(avg_kp,1),
                "GoldEfficiency(%)": round(gold_eff,1)
            })

        player_df = pd.DataFrame(player_rows)
        st.subheader("Moyennes par joueur")
        st.dataframe(player_df, hide_index=True)

        # -------------------------------------------------------
        # Répartition par Rôle (Gold & Damage)
        # -------------------------------------------------------
        role_data_gold   = []
        role_data_damage = []

        gold_tot = 0.0
        dmg_tot  = 0.0

        # Sommes moyennes par rôle
        for role in data_roles:
            gold_mean = data_roles[role]["Gold"] / nb_matches_parsed
            dmg_mean  = data_roles[role]["Damage"] / nb_matches_parsed
            gold_tot += gold_mean
            dmg_tot  += dmg_mean

        # Table Gold par rôle
        for role in ["TOP","JUNGLE","MIDDLE","BOTTOM","UTILITY"]:
            gold_mean = data_roles[role]["Gold"] / nb_matches_parsed
            pct_g = (gold_mean / gold_tot * 100) if gold_tot > 0 else 0
            role_data_gold.append({
                "Rôle": role,
                "Gold": f"{gold_mean:,.0f}",
                "Pourcentage (%)": round(pct_g, 2)
            })

        role_data_gold.append({
            "Rôle": "Total",
            "Gold": f"{gold_tot:,.0f}",
            "Pourcentage (%)": 100.0
        })

        # Table Damage par rôle
        for role in ["TOP","JUNGLE","MIDDLE","BOTTOM","UTILITY"]:
            dmg_mean  = data_roles[role]["Damage"] / nb_matches_parsed
            pct_d = (dmg_mean / dmg_tot * 100) if dmg_tot > 0 else 0
            role_data_damage.append({
                "Rôle": role,
                "Damage": f"{dmg_mean:,.0f}",
                "Pourcentage (%)": round(pct_d, 2)
            })

        role_data_damage.append({
            "Rôle": "Total",
            "Damage": f"{dmg_tot:,.0f}",
            "Pourcentage (%)": 100.0
        })

        df_gold   = pd.DataFrame(role_data_gold)
        df_damage = pd.DataFrame(role_data_damage)

        st.subheader("Répartition moyenne des Golds et Dégâts")
        col1, col2 = st.columns(2)

        with col1:
            st.write("**Moyenne de Gold par Rôle**")
            st.dataframe(df_gold, hide_index=True)

        with col2:
            st.write("**Moyenne de Dégâts par Rôle**")
            st.dataframe(df_damage, hide_index=True)
    
    # Onglet "Champions"
    with tab2:
        # On n'affiche les stats que si on les a calculées
        if 'champion_stats' in locals():
            display_champion_stats(champion_stats)
        else:
            st.warning("Veuillez d'abord charger les données dans l'onglet 'Statistiques générales'")

if __name__ == "__main__":
    main()
