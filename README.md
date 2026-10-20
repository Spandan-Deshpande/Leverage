# Leverage

**Explore the advantage in your next eight cards.**

Leverage is a local desktop app for Clash Royale deck analysis. Build decks by dragging cards into place, compare a matchup with a trained XGBoost model, explore card replacements, and search for a counter deck.

Built with Python and PySide6, the app includes a library of **102 cards**, card artwork, a pretrained model for local inference, and a Windows executable. No Clash Royale account, API key, or hosted prediction service is required by the source application.

### Run on Windows

Download the Windows executable (`Leverage.exe`) using Git LFS and launch it directly.

The executable is self-contained and includes the trained XGBoost model, card data, artwork, Python runtime, and required dependencies. **No Python installation, separate model download, or additional setup is required.**

If cloning the repository, install Git LFS and run `git lfs pull` to retrieve the executable.

Windows may display a security warning because the executable is unsigned. Only run software from sources you trust.
## What you can do

| Tool | How it works |
| --- | --- |
| **Predict Winner** | Fill two eight-card decks and select **Compare Decks** to see which side the model favors. |
| **Deck Improvement** | Fill your deck, select a non-win-condition card, and request the top three replacement candidates. |
| **Counter Deck** | Enter an opponent's deck and search for a lineup with a higher predicted chance of winning that matchup. |

The interface prevents duplicate cards within a deck. Click a filled slot to clear it on the prediction and counter-deck pages; on the improvement page, clicking selects a card for replacement.

## Run from source

You need Python with `pip` and [Git LFS](https://git-lfs.com/) installed. Use a virtual environment to keep the app's dependencies separate from other projects.

The model is approximately **272 MiB** and the Windows executable is approximately **289 MiB**. Both are tracked with Git LFS. Clone this repository, open a terminal in its root, and download the large files:

```sh
git lfs install
git lfs pull
python -m venv .venv
```

Activate the environment:

**Windows PowerShell**

```powershell
.\.venv\Scripts\Activate.ps1
```

**macOS / Linux**

```sh
source .venv/bin/activate
```

Install the dependencies and launch:

```sh
python -m pip install -r code/requirements.txt
cd code
python main.py
```

Launch from the `code` directory: the current implementation resolves its model, card data, and artwork relative to the working directory. Keep their names and layout unchanged. A graphical desktop session is required. Platform compatibility and dependency installation have not been verified for this publication package.

If model loading fails after cloning, run `git lfs pull` from the repository root and confirm that the `.ubj` file contains the downloaded model rather than a small LFS pointer.

## How the model is used

Each matchup becomes a **264-value feature vector**:

- 102 card-presence indicators for each deck.
- 10 summary features for each deck, including rarity counts and average elixir.
- 20 summed card attributes for each deck, including damage, targeting, mobility, and strategic roles.

The app holds both sides at a trophy value of 6,000 and a total card level of 88 (eight cards at level 11). It loads the saved XGBoost booster once and uses CPU inference.

**Replacement search** evaluates eligible swaps against 15 randomly sampled opponent decks using a fixed seed. It keeps the existing win-condition cards and allows the deck's average elixir to increase by at most 1.0. The top three results are ranked by their mean prediction across those opponents; they are not guaranteed to improve on the original deck.

**Counter-deck search** starts from four random decks and makes improving single-card substitutions for up to five passes per start. Candidate substitutions are filtered to an average elixir of at most 5.0. Initial random decks are not checked against that cap, so the current implementation does not guarantee every returned deck meets it.

## Repository layout

```text
.
├── README.md
├── .gitignore
├── .gitattributes
├── Leverage.exe                      # Bundled Windows app, stored with Git LFS
├── Report.pdf                    # Project report
└── code/
    ├── main.py                         # Desktop interface and deck searches
    ├── shared.py                       # Data loading, features, and inference
    ├── requirements.txt               # Python dependencies
    ├── Clash_Royale_Card_Data_clean.csv
    ├── clash_royale_xgb_final.ubj       # Pretrained model, stored with Git LFS
    └── assets/
        └── cards/                     # 102 card images
```

## Scope and limitations

- Predictions are model estimates, not guaranteed outcomes or verified real-world win rates.
- The card library is a fixed snapshot of 102 cards; it does not update with balance changes or new releases.
- Replacement scores use randomly sampled decks, not a measured distribution of current competitive decks.
- Counter-deck generation is a heuristic search and may return different results between runs. It does not guarantee the best possible deck.
- The repository contains inference code and a trained model. Training scripts, raw battle data, and independently reproducible evaluation results are not included.
- The source app performs local inference and contains no explicit account login, network requests, or telemetry implementation.

## Publishing and large files

The included `.gitattributes` configures the model and executable for Git LFS. Run `git lfs install` **before staging either large file**. GitHub blocks ordinary Git files larger than 100 MiB; see [GitHub's large-file documentation](https://docs.github.com/en/repositories/working-with-files/managing-large-files/about-large-files-on-github).

The project report is included in its original form. The `.gitignore` excludes environment files, private keys, local settings, build outputs, and Python caches. Ignoring files does not remove files already committed to Git.

## Project status and assets

Leverage is an unofficial Clash Royale project and is not affiliated with or endorsed by Supercell. Clash Royale names and artwork belong to their respective owners.

No software license is included in this repository. Publication alone does not grant an open-source license; reuse of the code, model, data, and artwork remains subject to the applicable rights.
