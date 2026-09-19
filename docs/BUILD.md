# Build and publish

This repository is a GitHub profile README generator. The public repository contains generated SVGs and profile data; the original portrait stays local.

## Requirements

- Python 3.11+
- OpenCV (`pip install opencv-python`)
- Git

## Generate locally

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install opencv-python

make PORTRAIT="$HOME/Pictures/ekagra-portrait.jpg" generate
```

The pipeline is deterministic:

1. `prep_photo.py` segments the subject and emits a local transparent PNG.
2. `generate_portrait.py` samples the image to a fixed monospace grid and emits dark/light animated SVGs.
3. `generate_readme.py` renders the README from `profile.config.json`.
4. `validate.py` checks expected assets and prevents the source portrait from entering the repository.

## Publish

The profile repository must be public and named exactly as you github username. GitHub uses that matching repository name to render the profile README.

```bash
git add README.md profile.config.json profile.schema.json assets/hero scripts docs Makefile .gitignore .github
python3 scripts/validate.py
git commit -m "feat: rebuild animated engineering profile"
git push origin main
```

## Updating the profile

Edit `profile.config.json`, regenerate the README, then commit. For a new portrait, keep the new source file outside the repository and run the generator again.
