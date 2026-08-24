# Shared Presence Field

**Shared presence** measures how much of a building population is gathered at a
place in space, read directly from 3D point clouds. For a query point *x*, take the
distance *dᵢ(x)* to the nearest point of building *i*, turn it into a soft vote with
a Gaussian, and average the votes over all *N* buildings:

```
S(x) = (1 / N) · Σᵢ exp( −dᵢ(x)² / (2 σ²) )
```

The sum runs over **buildings, not points** — each building collapses to a single
nearest distance, so a densely scanned building does not count more than a sparse
one. That is "one building, one contribution." Values are unnormalised (never
rescaled within a dataset). σ sets how close two surfaces must lie to count as the
same place.

This repository contains the method and **five sample point clouds**, so you can run
it end to end and inspect the result.

## Quick start

**Requires Python 3.10 or later.** On Windows, when you install Python tick
**Add python.exe to PATH** in the installer, otherwise `run.bat` cannot find it.

- **Windows:** double-click **`run.bat`**
- **macOS / Linux:** `./run.sh`

Either one creates a local virtual environment, installs
`numpy` / `scipy` / `matplotlib`, runs the pipeline, and opens the `out/` folder.
First run takes a few minutes (mostly the install); after that it is under a minute.

In `out/` you get:

| file | what it is |
|---|---|
| `1_shared_cloud.png` | the five clouds merged, coloured and sized by shared presence — the payoff image |
| `2_height_profile.png` | shared presence against height above the floor datum |
| `3_per_building.png` | the five buildings ordered from shared to singular |
| `4_kernel_widths.png` | one building at σ = 0.08, 0.12, 0.20 m — σ is a reading scale |
| `shared_cloud.ply` + `A_spf.ply … E_spf.ply` | point clouds carrying a per-point `shared_presence` scalar; open in CloudCompare and colour with a ramp |
| `per_building.csv` | per-building median shared presence |

## The samples give N = 5, not the paper's numbers

Shared presence is defined over a whole population. The five samples are just five
buildings, so **the values the script prints are on a different scale from the
paper's and will not match them** — every point already scores at least 1/N = 0.2
from its own building. The published figures come from all 68 buildings; the samples
here demonstrate the method, not the result.

These five are a **convenience sample**, not a representative draw across the
settlement, and five buildings cannot reproduce a field defined over all 68 — so
this small field demonstrates the method and is not a miniature of the published
one.

## Alignment is not in this repository

For the published work the clouds were first brought into a common frame **by hand in
CloudCompare v2.13.2**. Each cloud is then translated in Python to a shared origin —
its footprint centre in plan, and its own 1st-percentile height as the floor (z = 0).
The samples are supplied **already in that frame**, and the code here begins from that
point. Running the method on your own clouds means aligning them first.

## σ = 0.12 m is fixed here

σ is held at 0.12 m and is **not re-selected** by the sample pipeline. In the paper,
0.12 m was chosen as the width that maximises the variation of per-building shared
presence *across all 68 buildings*. That selection is meaningful only on a full
population — run it on five buildings and it lands elsewhere. Applying the method to
another population means selecting σ again for that population.

## Data availability

Five buildings, voxel-downsampled to 2 cm, **XYZ only** (colour, normals and all
other fields removed), published under the letters **A–E**. The letters are a naming
convention, not anonymisation: these are exterior geometry, carry no geographic
coordinates, and each sits in its own local frame. The full set of 68 is **not**
released — the boathouses are private residences.