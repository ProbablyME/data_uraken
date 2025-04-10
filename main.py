import streamlit as st
import pandas as pd
import json
import os
import re
from datetime import datetime
from collections import Counter, defaultdict
import requests
from PIL import Image
from io import BytesIO
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np

# Configuration de la page
st.set_page_config(
    page_title="URAKEN Stats",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personnalisé
st.markdown("""
    <style>
    .main {
        padding: 2rem;
    }
    .stTitle {
        color: #FF4B4B;
        font-size: 3rem !important;
        font-weight: 700 !important;
        margin-bottom: 2rem !important;
        text-align: center;
    }
    .stSubheader {
        color: #1E88E5;
        font-size: 1.5rem !important;
        font-weight: 600 !important;
        margin-top: 2rem !important;
    }
    .stats-card {
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 1rem;
        margin: 0.5rem 0;
    }
    </style>
    """, unsafe_allow_html=True)

# -----------------------------
# 1. Paramètres communs
# -----------------------------

TEAM_PLAYERS = [
    "",
    "Peche le coquin",
    "ManGros Fish",
    "gumaguccy",
    "Cheikh Sadri"
]

# Pour un affichage plus lisible
DISPLAY_NAME = {
    "": "Nireo",
    "Peche le coquin": "Peche",
    "ManGros Fish": "Jawa",
    "gumaguccy": "kross",
    "Cheikh Sadri": "iench taric"
}

ROLE_MAPPING = {
    "TOP": "TOP",
    "JUNGLE": "JUNGLE",
    "MIDDLE": "MIDDLE",
    "MID": "MIDDLE",
    "BOTTOM": "BOTTOM",
    "BOT": "BOTTOM",
    "UTILITY": "UTILITY",
    "SUPPORT": "UTILITY"
}

def parse_date_from_filename(filename):
    """
    Extrait la date depuis un nom de fichier au format 'DD_MM_YYYY_GX.json'.
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
    ddragon_version = "15.1.1"  # À mettre à jour quand nécessaire
    # On formate le nom du champion pour qu'il corresponde à la convention DDragon
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
        displayed_name = DISPLAY_NAME.get(player, player)
        
        with cols[idx]:
            st.markdown(
                f"""
                <div style="
                    background-color: #1E1E1E;
                    border-radius: 10px;
                    padding: 15px;
                    margin-bottom: 20px;
                ">
                    <h3 style="
                        color: #FFFFFF;
                        font-size: 24px;
                        font-weight: bold;
                        text-align: center;
                        margin-bottom: 20px;
                        text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
                    ">{displayed_name}</h3>
                """,
                unsafe_allow_html=True
            )
            
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
                    # Calcul du winrate
                    winrate = 0
                    if stats['games'] > 0:
                        winrate = (stats['wins'] / stats['games']) * 100
                    
                    # Couleur du winrate
                    if winrate >= 60:
                        color = "#66BB6A"  # Vert
                    elif winrate >= 50:
                        color = "#FFA726"  # Orange
                    else:
                        color = "#FF4B4B"  # Rouge
                    
                    # Container pour chaque champion avec grille fixe
                    st.markdown(
                        f"""
                        <div style="
                            background-color: rgba(255,255,255,0.1);
                            border-radius: 8px;
                            padding: 12px;
                            margin: 8px 0;
                            border: 1px solid rgba(255,255,255,0.1);
                            display: grid;
                            grid-template-columns: 80px 1fr;
                            gap: 10px;
                            align-items: center;
                        ">
                            <div style="text-align: center;">
                        """,
                        unsafe_allow_html=True
                    )
                    
                    # Affichage de l'icône du champion
                    try:
                        icon_url = get_champion_icon_url(champ_name)
                        response = requests.get(icon_url)
                        img = Image.open(BytesIO(response.content))
                        st.image(img, width=60)
                    except:
                        st.markdown(f"<p style='color: #FFFFFF; font-size: 16px;'>{champ_name}</p>", unsafe_allow_html=True)
                    
                    st.markdown("</div>", unsafe_allow_html=True)
                    
                    # Affichage des stats avec mise en forme
                    st.markdown(
                        f"""
                        <div style="
                            text-align: left;
                            display: flex;
                            flex-direction: column;
                            justify-content: center;
                        ">
                            <h4 style="
                                color: #FFFFFF;
                                font-size: 18px;
                                font-weight: bold;
                                margin: 0 0 5px 0;
                            ">{champ_name}</h4>
                            <p style="
                                color: #CCCCCC;
                                font-size: 14px;
                                margin: 0 0 5px 0;
                            ">Parties: {stats['games']}</p>
                            <p style="
                                color: {color};
                                font-weight: bold;
                                font-size: 16px;
                                margin: 0 0 5px 0;
                            ">
                                Winrate: {winrate:.1f}%
                            </p>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                    
                    st.markdown("</div>", unsafe_allow_html=True)
                    
                    # Barre de progression pour le winrate
                    st.progress(winrate / 100)
            else:
                st.info("Pas de données")
            
            st.markdown('</div>', unsafe_allow_html=True)

# -------------------------------------------------------------
# 2. Début de l'application Streamlit avec création des onglets
# -------------------------------------------------------------
def main():
    st.title("Statistiques URAKEN")

    # Création des onglets
    tab1, tab2, tab3, tab4 = st.tabs(["Statistiques générales", "Champions", "Tournoi", "Drafts"])

    # ----------------------------------------------
    # Onglet 1 : Statistiques générales (Scrims)
    # ----------------------------------------------
    with tab1:
        # 1) Dossier JSON
        json_folder = "scrims_json"
        if not os.path.exists(json_folder):
            st.error(f"Le dossier '{json_folder}' n'existe pas.")
        else:
            # 2) Lister fichiers JSON + parse date
            all_files = [f for f in os.listdir(json_folder) if f.endswith(".json")]
            date_files = []
            for fname in all_files:
                file_date = parse_date_from_filename(fname)
                if file_date is None:
                    continue
                date_files.append((file_date, fname))

            if not date_files:
                st.warning("Aucun fichier JSON au format attendu trouvé.")
            else:
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

                total_first_blood_kills = 0
                total_first_blood_assists = 0
                total_team_damage = 0
                total_game_duration = 0

                # Early game stats
                total_team_cs_15 = 0
                total_team_gold_diff_15 = 0
                first_dragon_count = 0
                first_herald_count = 0

                # Vision stats
                total_team_vision_score = 0
                total_team_vision_per_min = 0
                total_control_wards = 0
                total_wards_killed = 0

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
                for d, fname in date_files:
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

                    from collections import Counter
                    c = Counter(team_candidates)
                    my_team = c.most_common(1)[0][0]  # ex: "100" ou "200"

                    # Vérifier si la team a gagné
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

                    # Stats d'équipe
                    for p in participants:
                        if p.get("TEAM") == my_team:
                            kills  = int(p.get("CHAMPIONS_KILLED", 0))
                            deaths = int(p.get("NUM_DEATHS", 0))
                            drakes = int(p.get("DRAGON_KILLS", 0))
                            barons = int(p.get("BARON_KILLS", 0))
                            herald = int(p.get("RIFT_HERALD_KILLS", 0))
                            towers = int(p.get("TURRET_TAKEDOWNS", 0))
                            grubs  = int(p.get("HORDE_KILLS", 0))
                            
                            # Nouvelles stats
                            game_duration = float(p.get("TIME_PLAYED", 0)) / 60  # en minutes
                            first_blood_kill = p.get("FIRST_BLOOD_KILL", False)
                            first_blood_assist = p.get("FIRST_BLOOD_ASSIST", False)
                            cs_per_min = int(p.get("MINIONS_KILLED", 0)) / game_duration if game_duration > 0 else 0
                            vision_per_min = int(p.get("VISION_SCORE", 0)) / game_duration if game_duration > 0 else 0
                            
                            # Stats à 15 minutes
                            cs_diff_15 = float(p.get("CS_DIFF_AT_15", 0))
                            gold_diff_15 = float(p.get("GOLD_DIFF_AT_15", 0))
                            xp_diff_15 = float(p.get("XP_DIFF_AT_15", 0))

                            match_team_kills  += kills
                            match_team_deaths += deaths
                            match_team_drakes += drakes
                            match_team_barons += barons
                            match_team_herald += herald
                            match_team_towers += towers
                            match_team_grubs  += grubs

                            # Mise à jour des stats first blood
                            if first_blood_kill:
                                total_first_blood_kills += 1
                            if first_blood_assist:
                                total_first_blood_assists += 1

                            # Mise à jour des dégâts et durée de partie
                            damage_to_champs = int(p.get("TOTAL_DAMAGE_DEALT_TO_CHAMPIONS", "0")) if p.get("TOTAL_DAMAGE_DEALT_TO_CHAMPIONS", "0").isdigit() else 0
                            total_team_damage += damage_to_champs
                            total_game_duration += game_duration

                            # Mise à jour des stats early game
                            cs_15 = float(p.get("MINIONS_KILLED_AT_15", "0")) if p.get("MINIONS_KILLED_AT_15", "0").replace(".", "").isdigit() else 0
                            gold_diff_15 = float(p.get("GOLD_DIFF_AT_15", "0")) if p.get("GOLD_DIFF_AT_15", "0").replace("-", "").replace(".", "").isdigit() else 0
                            
                            total_team_cs_15 += cs_15
                            total_team_gold_diff_15 += gold_diff_15

                            # First objectives
                            if p.get("FIRST_DRAGON_KILL", False):
                                first_dragon_count += 1
                            if p.get("FIRST_HERALD_KILL", False):
                                first_herald_count += 1

                            # Vision stats
                            vision_score = int(p.get("VISION_SCORE", "0")) if p.get("VISION_SCORE", "0").isdigit() else 0
                            control_wards = int(p.get("VISION_WARDS_BOUGHT_IN_GAME", "0")) if p.get("VISION_WARDS_BOUGHT_IN_GAME", "0").isdigit() else 0
                            wards_killed = int(p.get("WARDS_KILLED", "0")) if p.get("WARDS_KILLED", "0").isdigit() else 0
                            
                            total_team_vision_score += vision_score
                            total_control_wards += control_wards
                            total_wards_killed += wards_killed

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
                            continue

                        kills    = int(p.get("CHAMPIONS_KILLED", 0))
                        deaths   = int(p.get("NUM_DEATHS", 0))
                        assists  = int(p.get("ASSISTS", 0))
                        gold_val = int(p.get("GOLD_EARNED", "0")) if p.get("GOLD_EARNED", "0").isdigit() else 0
                        dmg_val  = int(p.get("TOTAL_DAMAGE_DEALT_TO_CHAMPIONS", "0")) if p.get("TOTAL_DAMAGE_DEALT_TO_CHAMPIONS", "0").isdigit() else 0

                        # Récupérer le nom du champion
                        champ_name = p.get("SKIN", "Unknown")

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
                else:
                    st.write(f"**Nombre de parties analysées : {nb_matches_parsed}**")

                    # -----------------------------
                    # Stats d'équipe => Moyennes avec visualisation améliorée
                    # -----------------------------
                    win_rate = (total_wins / nb_matches_parsed) * 100 if nb_matches_parsed > 0 else 0
                    avg_drakes  = total_drakes      / nb_matches_parsed
                    avg_barons  = total_barons      / nb_matches_parsed
                    avg_herald  = total_herald      / nb_matches_parsed
                    avg_towers  = total_towers      / nb_matches_parsed
                    avg_grubs   = total_grubs       / nb_matches_parsed
                    avg_kills   = total_team_kills  / nb_matches_parsed
                    avg_deaths  = total_team_deaths / nb_matches_parsed

                    # Affichage du Win Rate avec une jauge
                    fig_winrate = go.Figure(go.Indicator(
                        mode = "gauge+number",
                        value = win_rate,
                        domain = {'x': [0, 1], 'y': [0, 1]},
                        title = {'text': "Win Rate"},
                        gauge = {
                            'axis': {'range': [0, 100]},
                            'bar': {'color': "#1E88E5"},
                            'steps': [
                                {'range': [0, 40], 'color': "#FF4B4B"},
                                {'range': [40, 60], 'color': "#FFA726"},
                                {'range': [60, 100], 'color': "#66BB6A"}
                            ]
                        }
                    ))
                    st.plotly_chart(fig_winrate, use_container_width=True)

                    # Statistiques des objectifs en texte
                    st.subheader("Statistiques moyennes par partie")
                    
                    # Création de colonnes pour une meilleure organisation
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("#### Combat")
                        st.write(f"**K/D équipe :** {avg_kills:.1f} kills, {avg_deaths:.1f} morts")
                        st.write(f"**First Blood participation :** {(total_first_blood_kills + total_first_blood_assists) / nb_matches_parsed * 100:.1f}%")
                        st.write(f"**Dégâts moyens par minute :** {total_team_damage / total_game_duration:.0f}")
                    
                    with col2:
                        st.markdown("#### Objectifs")
                        st.write(f"**Mobs épiques :** {avg_drakes:.1f} dragons, {avg_barons:.1f} barons, {avg_herald:.1f} hérauts")
                        st.write(f"**Tours :** {avg_towers:.1f} tours détruites")
                        st.write(f"**Grubs :** {avg_grubs:.1f} grubs")
                    
                    # Statistiques de vision
                    st.markdown("#### Vision")
                    vision_col1, vision_col2 = st.columns(2)
                    
                    with vision_col1:
                        avg_vision_score = total_team_vision_score / nb_matches_parsed
                        avg_vision_per_min = total_team_vision_score / total_game_duration if total_game_duration > 0 else 0
                        st.write(f"**Score de vision moyen :** {avg_vision_score:.1f}")
                        st.write(f"**Vision par minute :** {avg_vision_per_min:.2f}")
                    
                    with vision_col2:
                        avg_control_wards = total_control_wards / nb_matches_parsed
                        avg_wards_killed = total_wards_killed / nb_matches_parsed
                        st.write(f"**Wards de contrôle achetées :** {avg_control_wards:.1f}")
                        st.write(f"**Wards ennemies détruites :** {avg_wards_killed:.1f}")

                    # -----------------------------
                    # Stats par joueur => Moyennes avec visualisation améliorée
                    # -----------------------------
                    st.subheader("Statistiques des joueurs")
                    
                    player_rows = []
                    player_stats_for_radar = defaultdict(dict)
                    
                    for name, stats in data_players.items():
                        nb = stats["NbGames"]
                        if nb == 0:
                            continue

                        displayed_name = DISPLAY_NAME.get(name, name)
                        avg_kills   = stats["Kills"]   / nb
                        avg_deaths  = stats["Deaths"]  / nb
                        avg_assists = stats["Assists"] / nb
                        avg_gold    = stats["Gold"]    / nb
                        avg_dmg     = stats["Damage"]  / nb
                        avg_kp      = stats["KP"]      / nb
                        kda = (stats["Kills"] + stats["Assists"]) / max(1, stats["Deaths"])
                        
                        # Nouvelles métriques
                        cs_per_min = stats.get("CS", 0) / stats.get("GameDuration", 1) if stats.get("GameDuration", 0) > 0 else 0
                        vision_per_min = stats.get("VisionScore", 0) / stats.get("GameDuration", 1) if stats.get("GameDuration", 0) > 0 else 0
                        dmg_per_min = avg_dmg / stats.get("GameDuration", 1) if stats.get("GameDuration", 0) > 0 else 0
                        avg_cs_diff_15 = stats.get("CSDiff15", 0) / nb if nb > 0 else 0
                        avg_gold_diff_15 = stats.get("GoldDiff15", 0) / nb if nb > 0 else 0

                        # Gold Efficiency approx
                        gold_eff = (avg_dmg / avg_gold) * 100 if avg_gold > 0 else 0

                        # Stockage pour le graphique radar avec nouvelles métriques
                        player_stats_for_radar[displayed_name] = {
                            'Kill Participation': avg_kp,
                            'Efficiency': gold_eff,
                            'KDA': kda,
                            'Assists/Game': avg_assists,
                            'Kills/Game': avg_kills
                        }

                        player_rows.append({
                            "Joueur": displayed_name,
                            "Parties": nb,
                            "KDA": round(kda, 2),
                            "Kills/Game": round(avg_kills, 1),
                            "Deaths/Game": round(avg_deaths, 1),
                            "Assists/Game": round(avg_assists, 1),
                            "KP (%)": round(avg_kp, 1),
                            "Gold Efficiency (%)": round(gold_eff, 1)
                        })

                    # Tableau des stats
                    player_df = pd.DataFrame(player_rows)
                    st.dataframe(
                        player_df.style.background_gradient(subset=['KDA', 'KP (%)', 'Gold Efficiency (%)'], cmap='Blues'),
                        hide_index=True,
                        use_container_width=True
                    )

                    # Graphiques radar pour chaque joueur
                    st.subheader("Profils des joueurs")
                    
                    # Définition des plages de valeurs pour chaque métrique
                    metric_ranges = {
                        'Kill Participation': {'min': 0, 'max': 100, 'good': 60},
                        'Efficiency': {'min': 0, 'max': 150, 'good': 100},
                        'KDA': {'min': 0, 'max': 5, 'good': 3},
                        'Assists/Game': {'min': 0, 'max': 15, 'good': 8},
                        'Kills/Game': {'min': 0, 'max': 10, 'good': 5}
                    }

                    # Ordre spécifique des métriques pour une meilleure lisibilité
                    metric_order = ['Kill Participation', 'Efficiency', 'KDA', 'Assists/Game', 'Kills/Game']

                    # Fonction de normalisation des valeurs
                    def normalize_value(value, metric_range):
                        min_val = metric_range['min']
                        max_val = metric_range['max']
                        normalized = min(max(value, min_val), max_val) / max_val * 100
                        return normalized

                    cols = st.columns(len(player_stats_for_radar))
                    
                    for idx, (player_name, stats) in enumerate(player_stats_for_radar.items()):
                        with cols[idx]:
                            # Normalisation des stats pour le radar
                            categories = metric_order
                            values = [normalize_value(stats[cat], metric_ranges[cat]) for cat in categories]
                            
                            fig = go.Figure()
                            
                            # Ajout des cercles de référence avec labels
                            for level in [25, 50, 75, 100]:
                                fig.add_trace(go.Scatterpolar(
                                    r=[level] * (len(categories) + 1),
                                    theta=categories + [categories[0]],
                                    fill=None,
                                    mode='lines',
                                    line=dict(color='rgba(255,255,255,0.1)'),
                                    showlegend=False,
                                    hoverinfo='skip'
                                ))
                            
                            # Ajout du profil du joueur
                            fig.add_trace(go.Scatterpolar(
                                r=values,
                                theta=categories,
                                fill='toself',
                                name=player_name,
                                fillcolor='rgba(29, 185, 84, 0.3)',  # Vert Spotify semi-transparent
                                line=dict(color='#1DB954'),  # Vert Spotify
                                text=[f"{stats[cat]:.1f}" for cat in categories],  # Valeurs réelles
                                hovertemplate="%{theta}: %{text}<br>Score: %{r:.1f}%<extra></extra>"
                            ))
                            
                            fig.update_layout(
                                polar=dict(
                                    radialaxis=dict(
                                        visible=True,
                                        range=[0, 100],
                                        showticklabels=False,
                                        gridcolor='rgba(255,255,255,0.1)'
                                    ),
                                    angularaxis=dict(
                                        gridcolor='rgba(255,255,255,0.1)',
                                        rotation=90,  # Rotation pour une meilleure lisibilité
                                        direction="clockwise"
                                    ),
                                    bgcolor='rgba(0,0,0,0)'
                                ),
                                showlegend=False,
                                title=dict(
                                    text=player_name,
                                    font=dict(size=20, color='white'),
                                    y=0.95
                                ),
                                paper_bgcolor='rgba(0,0,0,0)',
                                margin=dict(t=100, b=100),  # Plus d'espace en haut et en bas
                                height=400  # Hauteur fixe pour tous les graphiques
                            )
                            
                            st.plotly_chart(fig, use_container_width=True)

                    # -----------------------------
                    # Répartition par Rôle avec graphiques améliorés
                    # -----------------------------
                    st.subheader("Répartition des ressources par rôle")
                    
                    role_data = []
                    gold_tot = 0
                    dmg_tot = 0
                    
                    # Calcul des totaux
                    for role in data_roles:
                        gold_mean = data_roles[role]["Gold"] / nb_matches_parsed
                        dmg_mean = data_roles[role]["Damage"] / nb_matches_parsed
                        gold_tot += gold_mean
                        dmg_tot += dmg_mean
                    
                    # Préparation des données
                    for role in ["TOP", "JUNGLE", "MIDDLE", "BOTTOM", "UTILITY"]:
                        gold_mean = data_roles[role]["Gold"] / nb_matches_parsed
                        dmg_mean = data_roles[role]["Damage"] / nb_matches_parsed
                        gold_pct = (gold_mean / gold_tot * 100) if gold_tot > 0 else 0
                        dmg_pct = (dmg_mean / dmg_tot * 100) if dmg_tot > 0 else 0
                        
                        role_data.append({
                            "Rôle": role,
                            "Gold": gold_mean,
                            "Gold (%)": gold_pct,
                            "Damage": dmg_mean,
                            "Damage (%)": dmg_pct
                        })
                    
                    role_df = pd.DataFrame(role_data)
                    
                    # Création des graphiques en camembert
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        fig_gold = px.pie(
                            role_df,
                            values='Gold (%)',
                            names='Rôle',
                            title='Répartition du Gold par rôle',
                            color_discrete_sequence=px.colors.sequential.Blues
                        )
                        st.plotly_chart(fig_gold, use_container_width=True)
                    
                    with col2:
                        fig_dmg = px.pie(
                            role_df,
                            values='Damage (%)',
                            names='Rôle',
                            title='Répartition des dégâts par rôle',
                            color_discrete_sequence=px.colors.sequential.Reds
                        )
                        st.plotly_chart(fig_dmg, use_container_width=True)

    # ----------------------------------------------
    # Onglet 2 : Champions
    # ----------------------------------------------
    with tab2:
        # Ici on suppose que "champion_stats" est calculé dans tab1 (dans le code ci-dessus)
        # On vérifie qu'il existe pour ne pas avoir d'erreur si l'utilisateur n'a pas encore chargé de données
        if "champion_stats" in locals():
            display_champion_stats(champion_stats)
        else:
            st.warning("Veuillez d'abord charger les données dans l'onglet 'Statistiques générales'.")

    # ----------------------------------------------
    # Onglet 3 : Tournoi – Moyenne des stats (pas de date)
    # ----------------------------------------------
    with tab3:
        st.subheader("Tournoi – Moyennes de stats par joueur (tous matchs)")
        
        # Dossier où se trouvent les fichiers de tournoi
        tournament_folder = "tournoi_json"  # Changez si besoin
        
        if not os.path.exists(tournament_folder):
            st.error(f"Le dossier '{tournament_folder}' n'existe pas.")
        else:
            # On liste tous les .json
            tournament_files = [f for f in os.listdir(tournament_folder) if f.endswith(".json")]
            
            if not tournament_files:
                st.warning("Aucun fichier JSON de tournoi trouvé.")
            else:
                # Accumulateur des stats
                tournament_stats = []
                
                # Lecture de chaque fichier
                for fname in tournament_files:
                    path = os.path.join(tournament_folder, fname)
                    try:
                        with open(path, "r", encoding="utf-8") as f:
                            match_data = json.load(f)
                    except Exception as e:
                        st.error(f"Erreur lecture {fname} : {e}")
                        continue
                    
                    match_id = match_data.get("matchId", fname)
                    
                    # Parcours des participants
                    for p in match_data.get("participants", []):
                        name = p.get("NAME", "")
                        if name not in TEAM_PLAYERS:
                            continue
                        
                        # Extraction stats (avec fallback = 0)
                        gold = int(p.get("GOLD_EARNED", "0")) if p.get("GOLD_EARNED", "0").isdigit() else 0
                        dmg  = int(p.get("TOTAL_DAMAGE_DEALT_TO_CHAMPIONS", "0")) if p.get("TOTAL_DAMAGE_DEALT_TO_CHAMPIONS", "0").isdigit() else 0
                        vis_score = int(p.get("VISION_SCORE", "0")) if p.get("VISION_SCORE", "0").isdigit() else 0
                        ctrl_wards = int(p.get("VISION_WARDS_BOUGHT_IN_GAME", "0")) if p.get("VISION_WARDS_BOUGHT_IN_GAME", "0").isdigit() else 0
                        kills = int(p.get("CHAMPIONS_KILLED", "0")) if p.get("CHAMPIONS_KILLED", "0").isdigit() else 0
                        deaths = int(p.get("NUM_DEATHS", "0")) if p.get("NUM_DEATHS", "0").isdigit() else 0
                        assists = int(p.get("ASSISTS", "0")) if p.get("ASSISTS", "0").isdigit() else 0
                        
                        # Calcul du KDA
                        kda = (kills + assists) / max(1, deaths)
                        
                        # Ajout au DataFrame
                        tournament_stats.append({
                            "Match": match_id,
                            "Player": DISPLAY_NAME.get(name, name),
                            "Gold Earned": gold,
                            "Damage to Champs": dmg,
                            "Vision Score": vis_score,
                            "Control Wards": ctrl_wards,
                            "KDA": round(kda, 2),
                            "Kills": kills,
                            "Deaths": deaths,
                            "Assists": assists
                        })
                
                if not tournament_stats:
                    st.warning("Aucune donnée de tournoi trouvée pour vos joueurs.")
                else:
                    df_tournament = pd.DataFrame(tournament_stats)
                    
                    # Calcul des moyennes par joueur
                    avg_df = (
                        df_tournament
                            .groupby("Player", as_index=False)[["Gold Earned", "Damage to Champs", "Vision Score", "Control Wards", "KDA", "Kills", "Deaths", "Assists"]]
                            .mean()
                    )
                    
                    # Arrondir les valeurs
                    for col in avg_df.columns:
                        if col != "Player":
                            avg_df[col] = avg_df[col].round(2)
                    
                    st.markdown("### Moyennes globales (tous matchs de tournoi)")
                    
                    # Affichage avec style
                    st.dataframe(
                        avg_df.style.background_gradient(subset=['KDA', 'Vision Score', 'Damage to Champs'], cmap='Blues'),
                        hide_index=True,
                        use_container_width=True
                    )
                    
                    # Graphiques de performance
                    st.markdown("### Visualisation des performances")
                    
                    # Graphique radar pour les performances par joueur
                    fig = go.Figure()
                    
                    for player in avg_df["Player"]:
                        player_data = avg_df[avg_df["Player"] == player].iloc[0]
                        
                        # Normalisation des données pour le radar
                        categories = ['KDA', 'Vision Score', 'Damage to Champs', 'Gold Earned', 'Control Wards']
                        values = [player_data[cat] for cat in categories]
                        
                        # Normalisation des valeurs
                        max_values = avg_df[categories].max()
                        normalized_values = [val / max_val for val, max_val in zip(values, max_values)]
                        
                        fig.add_trace(go.Scatterpolar(
                            r=normalized_values,
                            theta=categories,
                            fill='toself',
                            name=player
                        ))
                    
                    fig.update_layout(
                        polar=dict(
                            radialaxis=dict(
                                visible=True,
                                range=[0, 1]
                            )),
                        showlegend=True,
                        title="Comparaison des performances par joueur"
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # (Optionnel) Bouton pour afficher le détail match par match
                    if st.checkbox("Afficher le détail match par match"):
                        st.markdown("### Détail complet")
                        st.dataframe(df_tournament, hide_index=True)

    # ----------------------------------------------
    # Onglet 4 : Drafts
    # ----------------------------------------------
    with tab4:
        st.subheader("Analyse des compositions")
        
        if not os.path.exists(json_folder):
            st.error(f"Le dossier '{json_folder}' n'existe pas.")
        else:
            # Structure pour stocker les drafts
            team_comps = []
            
            # Parcours des fichiers
            for d, fname in date_files:
                path = os.path.join(json_folder, fname)
                with open(path, "r", encoding="utf-8") as f:
                    match_data = json.load(f)

                participants = match_data.get("participants", [])
                if not participants:
                    continue

                # Identifier notre équipe
                team_candidates = []
                for p in participants:
                    player_name = p.get("NAME", "")
                    if player_name in TEAM_PLAYERS:
                        team_candidates.append(p.get("TEAM"))

                if not team_candidates:
                    continue

                c = Counter(team_candidates)
                my_team = c.most_common(1)[0][0]

                # Collecter le draft de notre équipe
                current_draft = {"TOP": "", "JUNGLE": "", "MIDDLE": "", "BOTTOM": "", "UTILITY": "", "Result": ""}
                for p in participants:
                    if p.get("TEAM") == my_team:
                        role_raw = p.get("TEAM_POSITION", "") or p.get("INDIVIDUAL_POSITION", "")
                        role = ROLE_MAPPING.get(role_raw.upper(), "")
                        if role:
                            champ = p.get("SKIN", "Unknown")
                            current_draft[role] = champ
                
                # Ajouter le résultat
                current_draft["Result"] = "Win" if any(
                    p.get("TEAM") == my_team and p.get("WIN", "").lower() == "win"
                    for p in participants
                ) else "Loss"
                
                team_comps.append(current_draft)

            if team_comps:
                # Compositions complètes les plus jouées
                st.markdown("### Compositions les plus jouées")
                
                # Convertir les drafts en tuples pour le comptage
                full_comps = Counter(
                    tuple(sorted((role, champ) for role, champ in comp.items() if role != "Result"))
                    for comp in team_comps
                )
                
                # Créer un DataFrame pour les comps
                comp_data = []
                for comp, count in full_comps.most_common():
                    # Calculer le winrate pour cette comp
                    wins = sum(1 for draft in team_comps 
                             if tuple(sorted((role, champ) for role, champ in draft.items() if role != "Result")) == comp 
                             and draft["Result"] == "Win")
                    winrate = (wins / count) * 100
                    
                    comp_dict = dict(comp)
                    comp_data.append({
                        "Games": count,
                        "Winrate": winrate,
                        "TOP": next((champ for role, champ in comp if role == "TOP"), ""),
                        "JUNGLE": next((champ for role, champ in comp if role == "JUNGLE"), ""),
                        "MIDDLE": next((champ for role, champ in comp if role == "MIDDLE"), ""),
                        "BOTTOM": next((champ for role, champ in comp if role == "BOTTOM"), ""),
                        "UTILITY": next((champ for role, champ in comp if role == "UTILITY"), "")
                    })
                
                if comp_data:
                    # Créer le DataFrame avec les données numériques
                    df_comps = pd.DataFrame(comp_data)
                    
                    # Trier par nombre de games puis par winrate
                    df_comps = df_comps.sort_values(['Games', 'Winrate'], ascending=[False, False])
                    
                    # Réorganiser les colonnes
                    column_order = ['Games', 'Winrate', 'TOP', 'JUNGLE', 'MIDDLE', 'BOTTOM', 'UTILITY']
                    df_comps = df_comps[column_order]
                    
                    # Appliquer le style sur les données numériques
                    styled_df = df_comps.style\
                        .background_gradient(subset=['Games'], cmap='Blues')\
                        .background_gradient(subset=['Winrate'], cmap='RdYlGn')
                    
                    # Formater le winrate en pourcentage après le style
                    styled_df = styled_df.format({
                        'Winrate': '{:.1f}%',
                        'Games': '{:.0f}'
                    })
                    
                    st.dataframe(
                        styled_df,
                        hide_index=True,
                        use_container_width=True
                    )
                else:
                    st.write("Pas de compositions complètes trouvées")

if __name__ == "__main__":
    main()
