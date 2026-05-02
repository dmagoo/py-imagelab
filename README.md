# py-imagelab

Evolves a target image by iteratively painting random shapes onto a canvas and keeping mutations that improve the match. Uses a genetic algorithm approach — each generation spawns N children, and the closest match to the target survives.

## Setup

Requires Python 3.8+.

```bash
python -m venv env
source env/bin/activate       # Windows: env\Scripts\activate
pip install -e .
```

## Tools

### imagemutate

Evolve a canvas toward a target image or movie.

```bash
imagemutate <target_path> [options]
```

Common options:

| Flag | Description |
|------|-------------|
| `-g N` | Stop at generation N (default 1000) |
| `-c N` | Children per generation (default 25) |
| `-r N` | Max shape radius (default 40) |
| `-S <shape>` | Shape type: circle, polygon, triangle, etc. |
| `-W word1 word2` | Use words instead of shapes |
| `-b img1 img2` | Use images as brushes inside shapes |
| `-i` | Save drawing instructions (JSON) instead of image — includes seed, run parameters, and full history for replay |
| `-d <dir>` | Output directory |
| `-N` | No display (headless) |
| `-v` | Verbose output |
| `--seed N` | Fix the random seed for reproducible runs |
| `--compare-strategy` | `euclidean` (default) or `lab` (perceptually weighted) |

While running:

| Key | Action |
|-----|--------|
| `Esc` | Quit |
| `Space` | Print stats to console |
| `S` | Save image |
| `A` | Save instructions file (JSON) |
| `Enter` | Save (uses default output mode) |
| `H` | Toggle highlight overlay (shows current working region) |
| `I` | Toggle info overlay (gen / child / radius on screen) |
| `←` / `→` | Decrease / increase children count |
| `↑` / `↓` | Increase / decrease max radius |
| `Shift` + arrow | Adjust by 10 instead of 1 |

### imagereplay

Replay a saved instructions file (`.json` output from `imagemutate -i`).

```bash
imagereplay <input_path> [options]
```

While running: arrow keys scrub through history, `Enter` saves current frame.

### imagemerge

Blend multiple images together.

```bash
imagemerge <image1> <image2> ... [options]
imagemerge <directory> [options]
```

| Flag | Description |
|------|-------------|
| `-o <file>` | Output file (extension sets format: png, jpg, bmp) |
| `-N` | No display |
