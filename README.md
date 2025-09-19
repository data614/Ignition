# Ignition Poker Assistant Prototype

This repository contains a small end-to-end prototype that demonstrates how a
real-time poker assistant could be built on top of screen captures.  The goal is
not to ship a production-grade bot but to provide a clean, well-structured
foundation that covers the three pillars outlined in the project brief:

1. **Screen capture** – grab only the pixels that matter using a predefined
   bounding box.
2. **OCR & detection** – convert the pixels into meaningful poker data such as
   hole cards, pot size, and stack sizes.
3. **Decision logic** – feed the structured state into a lightweight rule engine
   that produces an action recommendation.

> ⚠️ Many poker sites forbid real-time assistance.  Use this prototype for
> educational or post-game analysis purposes and at your own risk.

## Repository layout

```
ignition/
  capture.py       # wrappers for live capture (mss) or offline image playback
  config.py        # dataclasses and helpers for YAML/JSON table configs
  decision.py      # simple preflop rule engine + hand canonicalisation helpers
  detection.py     # card template matching utilities (OpenCV)
  ocr.py           # pytesseract wrapper with basic preprocessing
  pipeline.py      # high-level orchestration of capture → state → decision
  state.py         # data models for hero/opponent/table state snapshots
configs/
  sample_config.yaml   # example set of bounding boxes for a 6-max table
scripts/
  run_assistant.py     # command-line entry point for offline/live execution
```

## Getting started

1. **Install system dependencies**

   * Python 3.10+
   * Tesseract OCR engine (required by `pytesseract`)
   * Optional: a directory of 52 card template PNGs (for accurate card
     recognition)

2. **Install Python packages**

   ```bash
   pip install numpy pillow mss pytesseract opencv-python pyyaml
   ```

3. **Create or adapt a table configuration**

   Copy `configs/sample_config.yaml` and tweak the bounding boxes so they match
   your poker client.  Every coordinate is relative to the top-left corner of
   the `table_region` capture window.

4. **Collect reference screenshots (optional but recommended)**

   Take a few screenshots of the table with different card combinations and chip
   stacks.  You can then iterate quickly in offline mode without touching the
   live client.

## Running the prototype

### Offline mode (recommended for development)

Process one or more screenshots and print the parsed state plus the recommended
action:

```bash
python scripts/run_assistant.py \
  --config configs/sample_config.yaml \
  --screenshots path/to/table_001.png path/to/table_002.png
```

If you also have a directory of pre-cropped card templates, supply it via
`--templates` to enable template matching:

```bash
python scripts/run_assistant.py \
  --config configs/sample_config.yaml \
  --templates assets/card_templates \
  --screenshots path/to/table.png
```

### Live capture mode

Once the configuration and OCR/card recognition behave correctly on offline
screenshots, you can switch to live capture.  This requires the `mss` package
and runs the capture loop at the interval defined in the config
(`capture_interval_ms`, 500 ms by default).

```bash
python scripts/run_assistant.py --config configs/sample_config.yaml --live
```

Press **Ctrl+C** to exit the loop.  The script prints the interpreted table
state and the action recommendation after every frame.

## Extending the prototype

* Replace the rule-based engine in `ignition/decision.py` with your solver
  output or a machine learning model.
* Add per-site theme support by keeping multiple config files and template
  libraries.
* Persist captured states to disk (e.g., CSV or SQLite) for post-session
  analysis.
* Integrate a GUI overlay by subscribing to the `FrameInterpreter` results and
  rendering them in a separate window.

## Disclaimer

This code is provided for research and educational purposes only.  Always make
sure your usage complies with the terms of service of the poker room you play
on.  The authors accept no responsibility for misuse.
