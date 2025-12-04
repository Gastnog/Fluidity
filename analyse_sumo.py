import pandas as pd
import numpy as np
import itertools

# --- 1. Constantes et Paramètres ---
POSITION_FEU = -4.20
SEUIL_DECELERATION = -0.5
VITESSE_ARRET = 0.1
DF_MIN_TRV = -5.0
DF_MAX_TRV = 10.0
PAS_TEMPS_MIN = 0.1
SEUIL_DUREE_ARRET = 1.0  # NOUVEAU : Durée minimale d'arrêt pour valider le cycle (en secondes)

# --- 2. Chargement des Données et Prétraitement (inchangé) ---
print("Chargement des données...")
try:
    df = pd.read_csv('simulation_data.csv')
except FileNotFoundError:
    print("ERREUR : Fichier 'simulation_data.csv' non trouvé. Vérifiez le chemin d'accès.")
    exit()

df.columns = ['t', 'a', 'veh_id', 'pos_x', 'pos_y', 'v']
df['t'] = pd.to_numeric(df['t'], errors='coerce')
df['a'] = pd.to_numeric(df['a'], errors='coerce')
df['v'] = pd.to_numeric(df['v'], errors='coerce')
df = df.dropna(subset=['t']).copy()

# --- 3. Identification Leader (inchangé) ---
df['Df'] = POSITION_FEU - df['pos_x']


def is_leader(group):
    df_amont = group[group['Df'] > 0]
    if df_amont.empty:
        return pd.Series(0, index=group.index)
    min_df = df_amont['Df'].min()
    return (group['Df'] == min_df).astype(int)


df['Veh(f)'] = df.groupby('t', group_keys=False).apply(is_leader)

# --- 4. Identification des Cycles (Ajout du critère de durée) ---

df_leader = df[df['Veh(f)'] == 1].copy()

# Créer les masques de base
df_leader['Is_Braking'] = (df_leader['a'] < SEUIL_DECELERATION) & (df_leader['v'] > VITESSE_ARRET)
df_leader['Is_Stopped'] = df_leader['v'] <= VITESSE_ARRET

# A. Détecter Trv (Fin de l'arrêt)
df_leader['Trv_Event'] = ((df_leader['v'] > VITESSE_ARRET) &
                          (df_leader['v'].shift(1) <= VITESSE_ARRET) &
                          (df_leader['t'].diff() > 0) &
                          (df_leader['Df'] > DF_MIN_TRV) &
                          (df_leader['Df'] < DF_MAX_TRV)).astype(int)


# B. Détecter Tvr CANDIDAT (Début du freinage)
def get_tvr_candidates(group):
    braking_started = group['Is_Braking']
    return (braking_started & ~braking_started.shift(1).fillna(False)).astype(int)


df_leader['Tvr_Candidate'] = df_leader.groupby('veh_id', group_keys=False).apply(get_tvr_candidates)


# --- NOUVELLE ÉTAPE 4.5 : Filtrage de la Durée d'Arrêt ---

def filter_stop_duration(group):
    """
    Filtre les Trv et ne garde les Tvr_Candidate que si l'arrêt subséquent
    a duré au moins SEUIL_DUREE_ARRET secondes.
    """

    # 1. Identifier les débuts d'arrêt (Stop Start) et fins d'arrêt (Stop End)
    group['Stop_Start'] = (group['Is_Stopped'] & ~group['Is_Stopped'].shift(1).fillna(False)).astype(int)
    group['Stop_End'] = (~group['Is_Stopped'] & group['Is_Stopped'].shift(1).fillna(False)).astype(int)

    # Extraire les temps des événements
    stop_starts = group[group['Stop_Start'] == 1]['t'].tolist()
    stop_ends = group[group['Stop_End'] == 1]['t'].tolist()

    # 2. Matcher les débuts et fins pour calculer la durée
    valid_stop_starts = {}  # {Stop_Start_Time: Stop_End_Time}
    i, j = 0, 0

    # S'assurer que les listes sont bien alignées (un début suivi d'une fin)
    while i < len(stop_starts) and j < len(stop_ends):
        start_t = stop_starts[i]
        end_t = stop_ends[j]

        if end_t > start_t:
            duration = end_t - start_t
            if duration >= SEUIL_DUREE_ARRET:
                valid_stop_starts[start_t] = end_t
            i += 1
            j += 1
        elif end_t <= start_t:
            # Fin d'arrêt avant ou en même temps que le début -> erreur, on avance la fin
            j += 1
        else:
            i += 1

    # 3. Filtrer les Tvr et Trv

    # Un Tvr est valide si un Stop_Start_Valide (premier arrêt) se produit juste après.
    valid_tvr_times = []

    # Un Trv est valide s'il correspond à un Stop_End d'un arrêt valide.
    valid_trv_times = []

    # On utilise les Tvr_Candidate
    tvr_candidates = group[group['Tvr_Candidate'] == 1]['t'].tolist()
    trv_events = group[group['Trv_Event'] == 1]['t'].tolist()

    for start_t, end_t in valid_stop_starts.items():
        # Trouver le Tvr le plus proche et juste avant le Stop_Start
        closest_tvr = [t for t in tvr_candidates if t < start_t]
        if closest_tvr:
            valid_tvr_times.append(closest_tvr[-1])  # Le dernier Tvr juste avant l'arrêt

        # Le Trv valide est le même que le Stop_End de l'arrêt valide
        valid_trv_times.append(end_t)

    # Convertir en Series masques (pour le regroupement)
    group['Final_Tvr_Event'] = group['t'].isin(valid_tvr_times).astype(int)
    group['Final_Trv_Event'] = group['t'].isin(valid_trv_times).astype(int)

    return group


# Appliquer le nouveau filtre de durée
df_leader = df_leader.groupby('veh_id', group_keys=False).apply(filter_stop_duration)

# --- 5. Extraction de TOUS les Événements UNIQUES FILTRÉS ---

# Utiliser les nouvelles colonnes Final_Tvr_Event et Final_Trv_Event
trv_results = df_leader[df_leader['Final_Trv_Event'] == 1].groupby('veh_id')['t'].apply(list).reset_index(
    name='Trv_Times')
tvr_results = df_leader[df_leader['Final_Tvr_Event'] == 1].groupby('veh_id')['t'].apply(list).reset_index(
    name='Tvr_Times')

# --- 6. Fusion et Formatage du Résultat Final (Ligne Unique Chronologique) ---
final_df = pd.merge(trv_results, tvr_results, on='veh_id', how='outer')

for col in ['Trv_Times', 'Tvr_Times']:
    final_df[col] = final_df[col].apply(lambda x: x if isinstance(x, list) else [])

# 1. Collecter tous les événements FINAUX
all_events = []
for index, row in final_df.iterrows():
    veh_id = row['veh_id']
    for t in row['Tvr_Times']:
        all_events.append((t, 'Tvr', veh_id))
    for t in row['Trv_Times']:
        all_events.append((t, 'Trv', veh_id))

# 2. Vérification critique
if not all_events:
    print("-" * 100)
    print(f"ALERTE : Aucun événement Tvr/Trv n'a été détecté (critère d'arrêt > {SEUIL_DUREE_ARRET}s non rempli).")
    print("Vérifiez les seuils ou la durée de la simulation.")
    print("-" * 100)
    exit()

# 3. Trier et formater la sortie
all_events.sort(key=lambda x: x[0])
output_header = ["T" + str(i + 1) for i in range(len(all_events))]
output_times = [f"{t[1]}{t[2]}({t[0]:.1f})" for t in all_events]

# --- 7. Calcul des Durées Moyennes des Feux ---

# Extraire les listes de temps Tvr et Trv triées
tvr_times_all = sorted([t[0] for t in all_events if t[1] == 'Tvr'])
trv_times_all = sorted([t[0] for t in all_events if t[1] == 'Trv'])

md_fr_list = []  # Liste des durées (Trv - Tvr) pour estimer le Rouge
md_fv_list = []  # Liste des durées (Tvr(i+1) - Trv(i)) pour estimer le Vert

# A. Calcul de la Durée du Feu Rouge (MDfr) : T_rv - T_vr
# La liste `all_events` est triée, donc les Tvr et Trv doivent être couplés
# Nous supposons que le nombre de Tvr et Trv est le même ou que le dernier Tvr n'a pas de Trv correspondant (arrêt final)
for i in range(min(len(tvr_times_all), len(trv_times_all))):
    tvr = tvr_times_all[i]
    trv = trv_times_all[i]

    # La durée du rouge est le temps passé à l'arrêt (freinage -> redémarrage)
    md_fr = trv - tvr
    if md_fr > 0:
        md_fr_list.append(md_fr)

# B. Calcul de la Durée du Feu Vert (MDfv) : T_vr(i+1) - T_rv(i)
# Le vert est la période entre le redémarrage d'un véhicule et le freinage du suivant
if len(tvr_times_all) >= 2 and len(trv_times_all) >= 1:
    # On itère jusqu'à l'avant-dernier Trv
    for i in range(len(trv_times_all)):
        # On a besoin d'un Tvr suivant pour calculer le vert
        if i + 1 < len(tvr_times_all):
            trv = trv_times_all[i]
            tvr_next = tvr_times_all[i + 1]

            md_fv = tvr_next - trv
            if md_fv > 0:
                md_fv_list.append(md_fv)

# Calcul des moyennes
MDfr = np.mean(md_fr_list) if md_fr_list else 0
MDfv = np.mean(md_fv_list) if md_fv_list else 0

# --- 8. AFFICHAGE du Résultat dans la Console ---

print("-" * 100)
print("RÉSULTATS FINAUX (Tvr et Trv) :")
print(f"Logique : Seuls les cycles d'arrêt de plus de {SEUIL_DUREE_ARRET} secondes sont conservés.")
print("Format: Événements (Type, ID du véhicule, Temps) sur une seule ligne chronologique.")
print("-" * 100)

print(" ".join(output_header))
print(" ".join(output_times))

print("-" * 100)

print("ANALYSE DES DURÉES DE FEU (Estimations Basées sur le Comportement du Leader) :")
print(f"Durée Moyenne estimée du Feu ROUGE (MDfr = T_rv - T_vr) : {MDfr:.2f} secondes")
print(f"Durée Moyenne estimée du Feu VERT (MDfv = T_vr(i+1) - T_rv(i)) : {MDfv:.2f} secondes")

print("-" * 100)
print("Analyse terminée.")