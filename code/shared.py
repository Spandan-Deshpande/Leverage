import os
import sys
import numpy as np
import pandas as pd
import xgboost as xgb

def resource_path(relative_path):
    """Works both when running as a script AND when packaged as a standalone exe."""
    if hasattr(sys, '_MEIPASS'):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

CSV_PATH = resource_path("Clash_Royale_Card_Data_clean.csv")
CARD_IMG_DIR = resource_path("assets/cards")
MODEL_PATH = resource_path("clash_royale_xgb_final.ubj")

WIN_CONDITION_COL = 10
ELIXIR_COL = 0
TROPHY_PLACEHOLDER = 6000

# ... rest of shared.py stays exactly the same

# --- Loaded once, shared everywhere ---
cards_df = pd.read_csv(CSV_PATH)

booster = xgb.Booster()
booster.load_model(MODEL_PATH)
booster.set_param({'device': 'cpu'})

card_ids_sorted = sorted(cards_df['card_id'].unique())
card_to_idx = {cid: i for i, cid in enumerate(card_ids_sorted)}
n_cards = len(card_to_idx)

attr_feature_cols = [
    'elixir_cost', 'damage', 'can_target_air', 'is_air_unit', 'is_splash',
    'movement_speed', 'is_ranged', 'range_value', 'troop_count', 'is_swarm',
    'is_win_condition', 'is_tank', 'is_mini_tank', 'is_building', 'is_spell',
    'is_support', 'is_defense', 'is_tank_killer', 'is_spawner', 'is_cycle'
]
cards_indexed = cards_df.set_index('card_id').loc[card_ids_sorted]
attr_matrix = cards_indexed[attr_feature_cols].values
rarity_lookup = cards_indexed['rarity'].values
name_lookup = cards_indexed['card_name'].to_dict()


def build_feature_row(p1_ids, p2_ids):
    p1_ids = [int(c) for c in p1_ids]
    p2_ids = [int(c) for c in p2_ids]

    def encode_multihot(ids):
        vec = np.zeros(n_cards, dtype=np.float32)
        for cid in ids:
            idx = card_to_idx.get(cid)
            if idx is not None:
                vec[idx] = 1
        return vec

    def numeric_features(ids):
        idxs = [card_to_idx[c] for c in ids]
        attrs = attr_matrix[idxs]
        rarities = rarity_lookup[idxs]
        is_building_count = attrs[:, 13].sum()
        is_spell_count = attrs[:, 14].sum()
        troop_count_approx = 8 - is_building_count - is_spell_count
        elixir_avg = attrs[:, ELIXIR_COL].mean()
        common_count = np.sum(rarities == "Common")
        rare_count = np.sum(rarities == "Rare")
        epic_count = np.sum(rarities == "Epic")
        legendary_count = np.sum(rarities == "Legendary")
        total_level = 11 * 8
        return np.array([
            total_level, troop_count_approx, is_building_count, is_spell_count,
            common_count, rare_count, epic_count, legendary_count,
            elixir_avg, TROPHY_PLACEHOLDER
        ], dtype=np.float32)

    def attr_sum(ids):
        idxs = [card_to_idx[c] for c in ids]
        return attr_matrix[idxs].sum(axis=0).astype(np.float32)

    return np.concatenate([
        encode_multihot(p1_ids), encode_multihot(p2_ids),
        numeric_features(p1_ids), numeric_features(p2_ids),
        attr_sum(p1_ids), attr_sum(p2_ids)
    ])


def predict_winner(p1_ids, p2_ids):
    row = build_feature_row(p1_ids, p2_ids).reshape(1, -1)
    return booster.predict(xgb.DMatrix(row))[0]


def is_win_condition(card_id):
    return attr_matrix[card_to_idx[int(card_id)], WIN_CONDITION_COL] == 1


def get_elixir(card_id):
    return attr_matrix[card_to_idx[int(card_id)], ELIXIR_COL]