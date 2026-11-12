# LED art

The top-level README's banner and skill icons are animated SVGs drawn as an amber dot-matrix
board, and `RECOMMENDED.md` uses the same board in cyan. `led.py` draws all of them from code,
along with the static social preview.

| File | Shows |
| --- | --- |
| `assets/banner.svg` | `council-debate` and `hill-climb` either side of the title |
| `assets/<skill>/icon.svg` | One loop per skill, on a square 25 x 25 board |
| `assets/recommended/banner.svg` | `RECOMMENDED.md`'s title between `thermo-nuclear-code-quality-review` and `bro` |
| `assets/recommended/<skill>/icon.svg` | The same for each skill in `RECOMMENDED.md`, in cyan so they read as someone else's |
| `assets/skillsfile/demo.svg` | The install section's `skillsfile` card: repos, a pinned `skills.yaml`, installed skills, and a patch that survives an update |
| `assets/social-preview.png` | 1280 x 640 still for the repository's social preview |

Each animation is a list of frames. Frames switch on instantly and fade out over 260 ms, so a
moving dot leaves a short trail. With reduced motion on, each one shows a finished frame and
stays still.

## Regenerate

```bash
python3 assets/led/led.py         # icons and banner
python3 assets/led/led.py --png   # also the social preview, needs Chrome
```

Upload `social-preview.png` by hand under Settings > General > Social preview; GitHub does not
read it from the repository.
