# py-imagelab

Evolves a target image by iteratively painting random shapes onto a canvas and keeping mutations that improve the match. Uses a genetic algorithm approach — each generation spawns N children, and the closest match to the target survives.

**How it works:** py-imagelab is a blind evolutionary process — a million monkeys painting at random, kept honest by a simple rule: only improvements survive. Every shape placed is genuinely random; the algorithm has no knowledge of the target beyond a pixel-level score. The result is emergent, not directed.

If you'd rather produce great-looking output faster than simulate evolution faithfully, `--adaptive-cheat-mode` scales radius and children automatically as the image converges — smaller shapes, more attempts, better late-run results. It works. It just isn't pure.

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
| `-j N` | Use N parallel worker processes for child generation (default: 1, serial); brief startup cost on first generation; most beneficial on longer runs; end-of-run stats include worker utilization. **Note:** the display may feel sluggish during each generation while workers compute — this is expected. |
| `--adaptive-cheat-mode` | Scale radius down and children up as match % improves — better art, less pure simulation |
| `--min-radius N` | Floor for adaptive radius (default: `max(radius // 8, 5)`) |
| `--save-on-exit` | Automatically save output when evolution completes |
| `--close-on-exit` | Close the display immediately when evolution completes (default: stay open) |

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

## Examples

```bash
# Basic run — circles, 1000 generations
imagemutate sample/images/fox-720x1080.jpg -d output -r 150 -c 100 -g 1000

# Parallel — 8 workers, best for longer runs
imagemutate sample/images/fox-720x1080.jpg -d output -r 150 -c 100 -g 1000 -j 8

# Perceptual color scoring
imagemutate sample/images/fox-720x1080.jpg -d output -r 150 -c 100 -g 1000 -j 8 --compare-strategy lab

# Triangles instead of circles
imagemutate sample/images/fox-720x1080.jpg -d output -r 150 -c 100 -g 1000 -j 8 -S triangle

# Words as shapes
imagemutate sample/images/fox-720x1080.jpg -d output -r 150 -c 100 -g 1000 -j 8 -W f o x

# Use another image as a brush texture inside shapes
imagemutate sample/images/fox-720x1080.jpg -d output -r 150 -c 100 -g 1000 -j 8 -b sample/images/oranges.jpg

# Reproducible run with fixed seed
imagemutate sample/images/fox-720x1080.jpg -d output -r 150 -c 100 -g 1000 --seed 42

# Save instructions for replay instead of image
imagemutate sample/images/fox-720x1080.jpg -d output -r 150 -c 100 -g 1000 -i

# Adaptive cheat mode — converges faster, looks better, less pure
imagemutate sample/images/fox-720x1080.jpg -d output -r 150 -c 100 -g 1000 -j 8 --adaptive-cheat-mode
```

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
