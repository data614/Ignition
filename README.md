# Ignition Poker Study Assistant

Ignition is a study-mode poker assistant focused on Ignition Casino style NLHE cash
games. It provides a lightweight command line coach for preflop range work and
simple post-flop heuristics so that players can review hands away from the tables
and stay compliant with site terms of service.

## Features

- Preflop range lookup for 6-max 100bb games with curated open, defend and
  re-raise charts.
- Post-flop heuristic engine that classifies hand strength, recognises basic
  draws and suggests actions using a discrete action set.
- Estimated equity versus a solid opponent range and short rationale text for
  each recommendation to encourage understanding instead of pure memorisation.

## Getting Started

The assistant is implemented in pure Python. Run the CLI from the repository root:

```bash
python -m ignition.cli --stage preflop --position CO --stack 100 --hand AsKd
```

Example post-flop usage:

```bash
python -m ignition.cli \
  --stage flop \
  --position BTN \
  --stack 100 \
  --pot 9 \
  --hand AsQs \
  --board Td8s3s
```

### Arguments

| Flag | Description |
| ---- | ----------- |
| `--stage` | Game stage (`preflop`, `flop`, `turn`, `river`). |
| `--position` | Hero position (`UTG`, `HJ`, `CO`, `BTN`, `SB`, `BB`). |
| `--stack` | Effective stack in big blinds (used for SPR and range selection). |
| `--pot` | Pot size in big blinds (post-flop only). |
| `--hand` | Hero hole cards, e.g. `AsKd`. |
| `--board` | Community cards, e.g. `AhKdTs` for the flop. |
| `--situation` | Preflop context (`open`, `vs_raise`, `vs_3bet`). |

## Project Structure

- `ignition/cards.py` – parsing helpers and canonical hand notation.
- `ignition/range_engine.py` – loads curated JSON ranges and returns preflop
  actions.
- `ignition/postflop.py` – board texture analysis and heuristic recommendations.
- `ignition/poker_assistant.py` – high-level facade combining both modules.
- `ignition/data/preflop_ranges.json` – 100bb 6-max preflop ranges used by the coach.

## Roadmap

The current version is designed for offline study. Future improvements could
include:

- Additional stack depths (40bb, 60bb) and tournament antes.
- Turn and river node solving distilled from full solvers to refine the
  heuristic engine.
- Range visualisation UI and heatmaps backed by the JSON data.
- Opt-in hand history logging for personalised leak analysis.
