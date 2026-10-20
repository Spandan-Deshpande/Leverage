import sys
import numpy as np
import xgboost as xgb
from PySide6.QtWidgets import (
    QApplication, QWidget, QLabel, QVBoxLayout, QHBoxLayout,
    QPushButton, QStackedWidget, QGridLayout, QScrollArea
)
from PySide6.QtCore import Qt, QMimeData
from PySide6.QtGui import QDrag, QPixmap

import shared


# ---------- Shared, reusable widgets ----------

class DraggableCard(QLabel):
    def __init__(self, card_id, card_name, parent=None):
        super().__init__(parent)
        self.card_id = str(card_id)
        self.card_name = card_name
        self.setFixedSize(70, 88)
        pixmap = QPixmap(f"{shared.CARD_IMG_DIR}/{self.card_id}.png")
        pixmap = pixmap.scaled(60, 78, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.setPixmap(pixmap)
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet("background-color: #1e1e1e; border-radius: 6px;")
        self.setToolTip(card_name)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            drag = QDrag(self)
            mime_data = QMimeData()
            mime_data.setText(self.card_id)
            drag.setMimeData(mime_data)
            drag.setPixmap(self.grab())
            drag.setHotSpot(event.position().toPoint())
            drag.exec(Qt.MoveAction)


class CardPalette(QScrollArea):
    def __init__(self):
        super().__init__()
        self.setWidgetResizable(True)
        self.setStyleSheet("background-color: black; border: none;")
        container = QWidget()
        grid = QGridLayout(container)
        grid.setSpacing(6)
        row, col = 0, 0
        for _, row_data in shared.cards_df.iterrows():
            card = DraggableCard(row_data["card_id"], row_data["card_name"])
            grid.addWidget(card, row, col)
            col += 1
            if col >= 6:
                col = 0
                row += 1
        self.setWidget(container)


class DeckSlot(QLabel):
    """
    Generic deck slot used across all three pages.
    side: "player" (blue outline) or "opponent" (red outline)
    clickable_mode: "clear" (click empties the slot) or "select" (click highlights it gold, used for Deck Improvement)
    """
    def __init__(self, side="player", clickable_mode="clear", on_select=None):
        super().__init__()
        self.card_id = None
        self.side = side
        self.clickable_mode = clickable_mode
        self.on_select = on_select
        self.selected = False
        self.siblings = []  # set externally after all slots in a deck are created
        self.setFixedSize(70, 88)
        self.setAlignment(Qt.AlignCenter)
        self.reset_style()
        self.setAcceptDrops(True)

    def outline_color(self):
        if self.selected:
            return "#ffcc00"
        return "#2255aa" if self.side == "player" else "#aa2222"

    def reset_style(self):
        self.setStyleSheet(
            f"background-color: #222222; border: 3px solid {self.outline_color()}; border-radius: 6px;"
        )

    def clear(self):
        self.card_id = None
        self.selected = False
        self.setPixmap(QPixmap())
        self.reset_style()

    def set_card(self, card_id):
        self.card_id = card_id
        pixmap = QPixmap(f"{shared.CARD_IMG_DIR}/{card_id}.png")
        pixmap = pixmap.scaled(60, 78, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.setPixmap(pixmap)
        self.reset_style()

    def dragEnterEvent(self, event):
        event.acceptProposedAction()

    def dropEvent(self, event):
        new_card_id = event.mimeData().text()
        for sib in self.siblings:
            if sib is not self and sib.card_id == new_card_id:
                event.ignore()
                return
        self.set_card(new_card_id)
        event.acceptProposedAction()

    def mousePressEvent(self, event):
        if event.button() != Qt.LeftButton or self.card_id is None:
            return
        if self.clickable_mode == "clear":
            self.clear()
        elif self.clickable_mode == "select":
            if self.on_select:
                self.on_select(self)


def get_deck(slots):
    return [s.card_id for s in slots if s.card_id is not None]


# ---------- Home Page ----------

class HomePage(QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("background-color: black;")
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)

        title = QLabel("LEVERAGE")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: white; font-size: 64px; font-weight: bold; letter-spacing: 4px;")

        tagline = QLabel("Turn 33 million battles into your unfair advantage.")
        tagline.setAlignment(Qt.AlignCenter)
        tagline.setStyleSheet("color: #cccccc; font-size: 20px; font-weight: bold; margin-top: 16px;")

        moto = QLabel(
            "We analyzed 33 million matches, separating skill from deck performance\n"
            "to give you the leverage."
        )
        moto.setAlignment(Qt.AlignCenter)
        moto.setStyleSheet("color: #888888; font-size: 15px; margin-top: 10px;")

        layout.addWidget(title)
        layout.addWidget(tagline)
        layout.addWidget(moto)
        self.setLayout(layout)


# ---------- Predict Winner Page ----------

class PredictWinnerPage(QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("background-color: black;")

        main_layout = QHBoxLayout()

        palette_layout = QVBoxLayout()
        palette_title = QLabel("All Cards")
        palette_title.setStyleSheet("color: white; font-size: 16px; font-weight: bold;")
        palette_layout.addWidget(palette_title)
        palette_layout.addWidget(CardPalette())

        self.player_slots = [DeckSlot(side="player", clickable_mode="clear") for _ in range(8)]
        for s in self.player_slots:
            s.siblings = self.player_slots
        player_grid = QGridLayout()
        for i, slot in enumerate(self.player_slots):
            player_grid.addWidget(slot, i // 4, i % 4)
        player_title = QLabel("Your Deck")
        player_title.setStyleSheet("color: #2255aa; font-size: 16px; font-weight: bold;")
        player_layout = QVBoxLayout()
        player_layout.addWidget(player_title)
        player_layout.addLayout(player_grid)
        player_layout.addStretch()

        self.opponent_slots = [DeckSlot(side="opponent", clickable_mode="clear") for _ in range(8)]
        for s in self.opponent_slots:
            s.siblings = self.opponent_slots
        opponent_grid = QGridLayout()
        for i, slot in enumerate(self.opponent_slots):
            opponent_grid.addWidget(slot, i // 4, i % 4)
        opponent_title = QLabel("Opponent Deck")
        opponent_title.setStyleSheet("color: #aa2222; font-size: 16px; font-weight: bold;")
        opponent_layout = QVBoxLayout()
        opponent_layout.addWidget(opponent_title)
        opponent_layout.addLayout(opponent_grid)
        opponent_layout.addStretch()

        self.compare_button = QPushButton("Compare Decks")
        self.compare_button.setStyleSheet(
            "background-color: #333333; color: white; font-size: 14px; padding: 10px; border-radius: 6px;"
        )
        self.compare_button.clicked.connect(self.on_compare_clicked)

        self.result_label = QLabel("")
        self.result_label.setAlignment(Qt.AlignCenter)

        center_layout = QVBoxLayout()
        center_layout.addStretch()
        center_layout.addWidget(self.compare_button)
        center_layout.addWidget(self.result_label)
        center_layout.addStretch()

        main_layout.addLayout(palette_layout, stretch=2)
        main_layout.addLayout(player_layout, stretch=1)
        main_layout.addLayout(opponent_layout, stretch=1)
        main_layout.addLayout(center_layout, stretch=1)
        self.setLayout(main_layout)

    def on_compare_clicked(self):
        p1_deck = get_deck(self.player_slots)
        p2_deck = get_deck(self.opponent_slots)
        if len(p1_deck) < 8 or len(p2_deck) < 8:
            self.result_label.setText("Both decks need 8 cards")
            self.result_label.setStyleSheet("color: #ffaa00; font-size: 16px; font-weight: bold;")
            return
        prob = shared.predict_winner(p1_deck, p2_deck)
        if prob >= 0.5:
            self.result_label.setText(f"Your deck favored: {prob:.1%} chance to win")
            self.result_label.setStyleSheet("color: #2255aa; font-size: 18px; font-weight: bold;")
        else:
            self.result_label.setText(f"Opponent favored: {1-prob:.1%} chance to win")
            self.result_label.setStyleSheet("color: #aa2222; font-size: 18px; font-weight: bold;")


# ---------- Deck Improvement Page ----------

class DeckImprovementPage(QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("background-color: black;")

        main_layout = QHBoxLayout()

        palette_layout = QVBoxLayout()
        palette_title = QLabel("All Cards")
        palette_title.setStyleSheet("color: white; font-size: 16px; font-weight: bold;")
        palette_layout.addWidget(palette_title)
        palette_layout.addWidget(CardPalette())

        self.player_slots = [
            DeckSlot(side="player", clickable_mode="select", on_select=self.on_slot_selected)
            for _ in range(8)
        ]
        for s in self.player_slots:
            s.siblings = self.player_slots
        deck_grid = QGridLayout()
        for i, slot in enumerate(self.player_slots):
            deck_grid.addWidget(slot, i // 4, i % 4)
        deck_title = QLabel("Your Deck (click a non-win-condition card to select it)")
        deck_title.setStyleSheet("color: #2255aa; font-size: 16px; font-weight: bold;")
        deck_layout = QVBoxLayout()
        deck_layout.addWidget(deck_title)
        deck_layout.addLayout(deck_grid)
        deck_layout.addStretch()

        self.result_slots = []
        self.result_labels = []
        result_col_layout = QVBoxLayout()
        for _ in range(3):
            row_layout = QHBoxLayout()
            slot = QLabel()
            slot.setFixedSize(70, 88)
            slot.setStyleSheet("background-color: #222222; border: 3px solid #ffcc00; border-radius: 6px;")
            label = QLabel("")
            label.setStyleSheet("color: white; font-size: 12px;")
            row_layout.addWidget(slot)
            row_layout.addWidget(label)
            result_col_layout.addLayout(row_layout)
            self.result_slots.append(slot)
            self.result_labels.append(label)

        self.suggest_button = QPushButton("Suggest Replacements")
        self.suggest_button.setStyleSheet(
            "background-color: #333333; color: white; font-size: 14px; padding: 10px; border-radius: 6px;"
        )
        self.suggest_button.clicked.connect(self.on_suggest_clicked)

        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignLeft)

        result_title = QLabel("Top 3 Replacements")
        result_title.setStyleSheet("color: #ffcc00; font-size: 16px; font-weight: bold;")
        result_layout = QVBoxLayout()
        result_layout.addWidget(result_title)
        result_layout.addLayout(result_col_layout)
        result_layout.addWidget(self.suggest_button)
        result_layout.addWidget(self.status_label)
        result_layout.addStretch()

        main_layout.addLayout(palette_layout, stretch=2)
        main_layout.addLayout(deck_layout, stretch=1)
        main_layout.addLayout(result_layout, stretch=1)
        self.setLayout(main_layout)

    def on_slot_selected(self, slot):
        if shared.is_win_condition(slot.card_id):
            self.status_label.setText("Win conditions cannot be selected for replacement")
            self.status_label.setStyleSheet("color: #ff5555; font-size: 14px; font-weight: bold;")
            return
        for s in self.player_slots:
            s.selected = False
            s.reset_style()
        slot.selected = True
        slot.reset_style()
        name = shared.name_lookup[int(slot.card_id)]
        self.status_label.setText(f"Selected: {name}. Click 'Suggest Replacements'.")
        self.status_label.setStyleSheet("color: #ffcc00; font-size: 14px;")

    def on_suggest_clicked(self):
        deck = [int(c) for c in get_deck(self.player_slots)]
        if len(deck) < 8:
            self.status_label.setText("Deck needs 8 cards")
            self.status_label.setStyleSheet("color: #ffaa00; font-size: 14px;")
            return

        selected = [i for i, s in enumerate(self.player_slots) if s.selected]
        if not selected:
            self.status_label.setText("Click a non-win-condition card in your deck first")
            self.status_label.setStyleSheet("color: #ffaa00; font-size: 14px;")
            return

        slot_index = selected[0]
        self.status_label.setText("Analyzing replacements...")
        QApplication.processEvents()

        result, error = self.suggest_replacements(deck, slot_index)

        for slot, label in zip(self.result_slots, self.result_labels):
            slot.setPixmap(QPixmap())
            label.setText("")

        if error:
            self.status_label.setText(error)
            self.status_label.setStyleSheet("color: #ff5555; font-size: 14px; font-weight: bold;")
            return

        baseline_score, top_candidates = result
        for i, (card_id, score) in enumerate(top_candidates):
            pixmap = QPixmap(f"{shared.CARD_IMG_DIR}/{card_id}.png")
            pixmap = pixmap.scaled(60, 78, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.result_slots[i].setPixmap(pixmap)
            self.result_labels[i].setText(f"{shared.name_lookup[card_id]}\n{score:.1%}")

        self.status_label.setText(f"Current deck strength: {baseline_score:.1%}")
        self.status_label.setStyleSheet("color: #2255aa; font-size: 16px; font-weight: bold;")

    def suggest_replacements(self, current_deck, slot_index, n_samples=15, max_elixir_increase=1.0, top_n=3):
        all_card_ids = list(shared.card_to_idx.keys())
        rng = np.random.RandomState(42)

        selected_card = current_deck[slot_index]
        if shared.is_win_condition(selected_card):
            return None, "Win conditions cannot be replaced."

        sample_opponents = [list(rng.choice(all_card_ids, size=8, replace=False)) for _ in range(n_samples)]

        original_elixir = shared.attr_matrix[
            [shared.card_to_idx[c] for c in current_deck], shared.ELIXIR_COL
        ].mean()
        candidate_ids = [c for c in all_card_ids if c not in current_deck]

        filtered = []
        for cid in candidate_ids:
            trial = current_deck.copy()
            trial[slot_index] = cid
            new_elixir = shared.attr_matrix[
                [shared.card_to_idx[c] for c in trial], shared.ELIXIR_COL
            ].mean()
            if new_elixir - original_elixir <= max_elixir_increase:
                filtered.append(cid)

        baseline_scores = [shared.predict_winner(current_deck, opp) for opp in sample_opponents]
        baseline_score = float(np.mean(baseline_scores))

        total_scores = np.zeros(len(filtered))
        for opp in sample_opponents:
            batch_rows = []
            for cid in filtered:
                trial = current_deck.copy()
                trial[slot_index] = cid
                batch_rows.append(shared.build_feature_row(trial, opp))
            batch_matrix = np.array(batch_rows)
            preds = shared.booster.predict(xgb.DMatrix(batch_matrix))
            total_scores += preds

        avg_scores = total_scores / n_samples
        ranked = sorted(zip(filtered, avg_scores), key=lambda x: x[1], reverse=True)
        return (baseline_score, ranked[:top_n]), None


# ---------- Counter Deck Page ----------

class CounterDeckPage(QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("background-color: black;")

        main_layout = QHBoxLayout()

        palette_layout = QVBoxLayout()
        palette_title = QLabel("All Cards")
        palette_title.setStyleSheet("color: white; font-size: 16px; font-weight: bold;")
        palette_layout.addWidget(palette_title)
        palette_layout.addWidget(CardPalette())

        self.opponent_slots = [DeckSlot(side="opponent", clickable_mode="clear") for _ in range(8)]
        for s in self.opponent_slots:
            s.siblings = self.opponent_slots
        opponent_grid = QGridLayout()
        for i, slot in enumerate(self.opponent_slots):
            opponent_grid.addWidget(slot, i // 4, i % 4)
        opponent_title = QLabel("Opponent Deck")
        opponent_title.setStyleSheet("color: #aa2222; font-size: 16px; font-weight: bold;")
        opponent_layout = QVBoxLayout()
        opponent_layout.addWidget(opponent_title)
        opponent_layout.addLayout(opponent_grid)
        opponent_layout.addStretch()

        self.result_slots = []
        result_grid = QGridLayout()
        for i in range(8):
            slot = QLabel()
            slot.setFixedSize(70, 88)
            slot.setStyleSheet("background-color: #222222; border: 3px solid #2255aa; border-radius: 6px;")
            self.result_slots.append(slot)
            result_grid.addWidget(slot, i // 4, i % 4)

        self.generate_button = QPushButton("Generate Counter Deck")
        self.generate_button.setStyleSheet(
            "background-color: #333333; color: white; font-size: 14px; padding: 10px; border-radius: 6px;"
        )
        self.generate_button.clicked.connect(self.on_generate_clicked)

        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignCenter)

        result_title = QLabel("Suggested Counter Deck")
        result_title.setStyleSheet("color: #2255aa; font-size: 16px; font-weight: bold;")
        result_layout = QVBoxLayout()
        result_layout.addWidget(result_title)
        result_layout.addLayout(result_grid)
        result_layout.addWidget(self.generate_button)
        result_layout.addWidget(self.status_label)
        result_layout.addStretch()

        main_layout.addLayout(palette_layout, stretch=2)
        main_layout.addLayout(opponent_layout, stretch=1)
        main_layout.addLayout(result_layout, stretch=1)
        self.setLayout(main_layout)

    def on_generate_clicked(self):
        opponent = get_deck(self.opponent_slots)
        if len(opponent) < 8:
            self.status_label.setText("Opponent deck needs 8 cards")
            self.status_label.setStyleSheet("color: #ffaa00; font-size: 14px;")
            return

        self.status_label.setText("Generating... this may take a few seconds")
        self.status_label.setStyleSheet("color: #cccccc; font-size: 14px;")
        QApplication.processEvents()

        def progress(restart, total):
            self.status_label.setText(f"Generating... attempt {restart}/{total}")
            QApplication.processEvents()

        best_deck, best_prob = self.build_counter_deck(opponent, elixir_cap=5.0, progress_callback=progress)

        for i, card_id in enumerate(best_deck):
            pixmap = QPixmap(f"{shared.CARD_IMG_DIR}/{card_id}.png")
            pixmap = pixmap.scaled(60, 78, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.result_slots[i].setPixmap(pixmap)

        self.status_label.setText(f"Predicted win rate: {best_prob:.1%}")
        self.status_label.setStyleSheet("color: #2255aa; font-size: 18px; font-weight: bold;")

    def build_counter_deck(self, opponent_deck_ids, elixir_cap=5.0, n_restarts=4, max_passes=5, progress_callback=None):
        all_card_ids = list(shared.card_to_idx.keys())
        rng = np.random.RandomState()
        best_deck_overall = None
        best_prob_overall = -1

        for restart in range(n_restarts):
            current_deck = list(rng.choice(all_card_ids, size=8, replace=False))
            for _pass in range(max_passes):
                improved = False
                for slot_i in range(8):
                    current_card = current_deck[slot_i]
                    best_candidate = current_card
                    best_prob = shared.predict_winner(current_deck, opponent_deck_ids)
                    for candidate in all_card_ids:
                        if candidate in current_deck:
                            continue
                        trial_deck = current_deck.copy()
                        trial_deck[slot_i] = candidate
                        avg_elixir = shared.attr_matrix[
                            [shared.card_to_idx[c] for c in trial_deck], shared.ELIXIR_COL
                        ].mean()
                        if avg_elixir > elixir_cap:
                            continue
                        prob = shared.predict_winner(trial_deck, opponent_deck_ids)
                        if prob > best_prob:
                            best_prob = prob
                            best_candidate = candidate
                    if best_candidate != current_card:
                        current_deck[slot_i] = best_candidate
                        improved = True
                if not improved:
                    break
            final_prob = shared.predict_winner(current_deck, opponent_deck_ids)
            if progress_callback:
                progress_callback(restart + 1, n_restarts)
            if final_prob > best_prob_overall:
                best_prob_overall = final_prob
                best_deck_overall = current_deck.copy()

        return best_deck_overall, best_prob_overall


# ---------- Sidebar ----------

class Sidebar(QWidget):
    def __init__(self, stacked_widget):
        super().__init__()
        self.setFixedWidth(220)
        self.setStyleSheet("background-color: #111111;")

        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignTop)
        layout.setContentsMargins(15, 30, 15, 15)
        layout.setSpacing(10)

        app_name = QLabel("LEVERAGE")
        app_name.setStyleSheet("color: white; font-size: 20px; font-weight: bold; margin-bottom: 20px;")
        layout.addWidget(app_name)

        buttons = [
            ("Home", 0),
            ("Predict Winner", 1),
            ("Deck Improvement", 2),
            ("Counter Deck", 3),
        ]

        for label, index in buttons:
            btn = QPushButton(label)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #1e1e1e;
                    color: white;
                    text-align: left;
                    padding: 12px;
                    border-radius: 6px;
                    font-size: 14px;
                }
                QPushButton:hover {
                    background-color: #2255aa;
                }
            """)
            btn.clicked.connect(lambda checked, i=index: stacked_widget.setCurrentIndex(i))
            layout.addWidget(btn)

        self.setLayout(layout)


# ---------- App entry point ----------

app = QApplication(sys.argv)

window = QWidget()
window.setWindowTitle("Leverage")
window.setStyleSheet("background-color: black;")

stacked_widget = QStackedWidget()
stacked_widget.addWidget(HomePage())
stacked_widget.addWidget(PredictWinnerPage())
stacked_widget.addWidget(DeckImprovementPage())
stacked_widget.addWidget(CounterDeckPage())

sidebar = Sidebar(stacked_widget)

main_layout = QHBoxLayout()
main_layout.setContentsMargins(0, 0, 0, 0)
main_layout.setSpacing(0)
main_layout.addWidget(sidebar)
main_layout.addWidget(stacked_widget)

window.setLayout(main_layout)
window.showMaximized()
sys.exit(app.exec())