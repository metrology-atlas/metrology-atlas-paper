"""Every kind of VitalDB time stamp as stored: bias against standard uncertainty (decision D4), and each corrected
source's standard uncertainty before and after correction. Read from the metrology atlas (one source of truth).

    python figures/src/fig_bias_uncertainty.py ATLAS_REPO figures/fig3-bias-uncertainty.pdf figures/fig3b-corrected-uncertainty.pdf

A. Forms as stored. Across: bias, the stamp minus the end of the interval its value describes, against the working
   reference (symmetric log axis, linear within 1 ms; left of zero the stamp comes early, look-ahead); the bar spans
   p5-p95 between recordings. Up: combined standard uncertainty (log). Solid marker measured, hollow estimated.
B. Corrected sources: standard uncertainty with the bias removed by a shift known in advance (the release median;
   or the as-stored spread where no shift is given), against after the per-recording correction (headline, an upper
   bound where so labelled; the likely value where two references exist).
"""
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

sys.path.insert(0, sys.argv[1])
from metrology_atlas import load  # noqa: E402
from metrology_atlas.timing import forms  # noqa: E402

INK, MUTED, GRID = "#1b2333", "#5a6170", "#e4e3df"
COL = {"waveform": "#2a78d6", "numeric": "#eb6834", "event": "#1baf7a", "text": "#8a6fd1"}
NAME = {"waveform": "Waveform samples", "numeric": "Numeric values", "event": "Records, lab and clinical times"}
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 7.5, "axes.edgecolor": MUTED,
                     "xtick.color": MUTED, "ytick.color": MUTED, "axes.labelcolor": INK})
ds = load(Path(sys.argv[1]) / "datasets" / "vitaldb")
V = ds.items["variable"]

# --- A: as stored -------------------------------------------------------------------------------------------------
rows = []
for vid, v in V.items():
    fv = forms(v)
    raw = any(f["kind"] == "as_stored" and f["name"] == "raw stamps" for f in fv)
    for f in fv:
        if f["kind"] == "as_stored" and (not raw or f["name"] == "raw stamps"):   # the stored stamps, where stated
            rows.append((v["name"] + ("" if f["name"] in ("as stamped", "as recorded", "raw stamps") else f" ({f['name']})"),
                         v["type"], f))
uniq = []
for r in sorted(rows, key=lambda r: r[2]["u_c"]):
    key = (r[2]["id"], round(r[2]["bias"]["mid"], 4), round(r[2]["u_c"], 4))
    hit = next((u for u in uniq if u[3] == key), None)
    if hit:
        hit[0] = hit[0].replace(" (SNUADC)", "") + ", " + r[0]
        continue
    uniq.append([r[0], r[1], r[2], key])
fig, ax = plt.subplots(figsize=(7.2, 5.0))
fig.subplots_adjust(left=0.1, right=0.98, top=0.98, bottom=0.22)
for i, (label, typ, f, _) in enumerate(uniq):
    b, c = f["bias"], COL.get(typ, "#888")
    measured = f["status"] == "measured"
    ax.plot([b["lo"], b["hi"]], [f["u_c"]] * 2, color=c, lw=1.4, alpha=0.6, solid_capstyle="butt")
    ax.plot(b["mid"], f["u_c"], "o", ms=5, color=c, mfc=c if measured else "white", mew=1.2)
ax.set_xscale("symlog", linthresh=1e-3, linscale=0.3)
ax.set_yscale("log")
ax.set_xlim(-3, 7200); ax.set_ylim(6e-3, 2.5e4)
# number labels placed so they do not overlap each other or the markers (display coordinates)
fig.canvas.draw()
pts = [ax.transData.transform((u[2]["bias"]["mid"], u[2]["u_c"])) for u in uniq]
placed = []
OFFS = [(4, 3), (4, -10), (-11, 3), (-11, -10), (4, 10), (-11, 10), (9, -3), (-16, -3), (4, -17), (-11, -17), (4, 17), (-11, 17)]
for i, (x0, y0) in enumerate(pts):
    w = 6.5 * len(str(i + 1)) * 0.8; h = 7
    for dx, dy in OFFS:
        box = (x0 + dx, y0 + dy, x0 + dx + w, y0 + dy + h)
        clash = any(not (box[2] < q[0] or box[0] > q[2] or box[3] < q[1] or box[1] > q[3]) for q in placed)
        clash = clash or any(box[0] - 3 < px < box[2] + 3 and box[1] - 3 < py < box[3] + 3 for px, py in pts)
        if not clash:
            break
    placed.append(box)
    ax.annotate(f"{i + 1}", (uniq[i][2]["bias"]["mid"], uniq[i][2]["u_c"]), xytext=(dx, dy), textcoords="offset points",
                fontsize=6.5, color=INK)
ticks = [-1, -0.1, -0.01, 0, 0.01, 0.1, 1, 10, 60, 600, 3600]
ax.set_xticks(ticks)
ax.set_xticklabels(["−1 s", "−100 ms", "−10 ms", "0", "10 ms", "100 ms", "1 s", "10 s", "1 min", "10 min", "1 h"])
ax.set_xlim(-3, 7200)
yt = [1e-2, 1e-1, 1, 10, 60, 600, 3600, 86400]
ax.set_yticks(yt); ax.set_yticklabels(["10 ms", "100 ms", "1 s", "10 s", "1 min", "10 min", "1 h", "1 d"])
ax.axvline(0, color=INK, lw=1.3, zorder=1)
ax.axvspan(-3, 0, color="#f3e7e1", alpha=0.5, lw=0)
ax.text(-2.6, 1.5e4, "stamp before the\nvalue could exist\n(look-ahead)", fontsize=6.5, color=MUTED, va="top")
ax.xaxis.set_minor_locator(matplotlib.ticker.SymmetricalLogLocator(linthresh=1e-3, base=10, subs=range(2, 10)))
ax.yaxis.set_minor_locator(matplotlib.ticker.LogLocator(base=10, subs=range(2, 10)))
ax.tick_params(which="minor", length=2, color=GRID)
ax.grid(which="major", color=GRID, lw=0.7); ax.grid(which="minor", color=GRID, lw=0.35, alpha=0.7); ax.set_axisbelow(True)
for s_ in ("top", "right"): ax.spines[s_].set_visible(False)
ax.set_xlabel("Bias: stamp minus the end of the interval the value describes (p5–p95 between recordings)")
ax.set_ylabel("Standard uncertainty (1 SD)")
for typ in ("waveform", "numeric", "event"):
    ax.plot([], [], "o", color=COL[typ], label=NAME[typ])
ax.plot([], [], "o", color=MUTED, mfc="white", label="estimated or assumed")
ax.legend(loc="lower right", frameon=False, fontsize=6.8)
key = "   ".join(f"{i + 1} {u[0]}" for i, u in enumerate(uniq))
fig.text(0.01, 0.005, "\n".join(__import__("textwrap").wrap(key, 150)), fontsize=5.8, color=INK, va="bottom")
fig.subplots_adjust(left=0.1, right=0.98, top=0.98, bottom=0.22)
fig.savefig(sys.argv[2])

# --- B: before and after correction ------------------------------------------------------------------------------
pairs = []
for vid, v in V.items():
    fs = forms(v)
    seen = {}
    for f in sorted(fs, key=lambda g: not g["default"]):
        if f["kind"] != "per_recording":
            continue
        before = [g for g in fs if g["id"] in f["corrects"] or (g["kind"] == "fixed_shift" and set(g["corrects"]) & set(f["corrects"]))]
        shifted = [g for g in before if g["kind"] == "fixed_shift"]
        b = (shifted or before)
        if not b: continue
        ub = min(g["u_c"] for g in b)
        k_v = (round(ub, 4), round(f["u_c"], 4))
        if not f["default"] and k_v in seen.values():
            continue          # same before and after as the signal's default form (e.g. differs only in drift rate)
        seen[f["id"]] = k_v
        short = {"draw time from arterial access": "draw time", "after sync with the recording's own bursts": "own bursts"}
        pairs.append((v["name"] + ("" if f["default"] else f" ({short.get(f['name'], f['name'])})"), v["type"], ub, f["u_c"], f["likely_u"], f["upper_bound"]))
P = []
for p in sorted(pairs, key=lambda p: p[3]):
    k = (round(p[2], 4), round(p[3], 4))
    hit = next((q for q in P if q[6] == k), None)
    if hit:
        hit[0] = hit[0].replace(" (SNUADC)", "") + ", " + p[0]
        continue
    P.append(list(p) + [k])
fig, ax = plt.subplots(figsize=(7.2, 0.3 * len(P) + 1.6))
for i, (label, typ, ub, ua, ul, upper, _) in enumerate(P):
    c = COL.get(typ, "#888")
    ax.plot([ua, ub], [i, i], color=c, lw=1.6, alpha=0.5)
    ax.plot(ub, i, "o", ms=5, color=MUTED, mfc="white", mew=1.2)
    ax.plot(ua, i, "o", ms=5.5, color=c)
    if upper: ax.annotate("≤", (ua, i), xytext=(-9, -3), textcoords="offset points", fontsize=7, color=c)
    if ul: ax.plot(ul, i, "D", ms=3.5, color=c, mfc="white")
ax.set_yticks(range(len(P))); ax.set_yticklabels([p[0] for p in P])
ax.set_xscale("log")
xt = [1e-3, 1e-2, 1e-1, 1, 10, 60, 600]
ax.set_xticks(xt); ax.set_xticklabels(["1 ms", "10 ms", "100 ms", "1 s", "10 s", "1 min", "10 min"])
ax.xaxis.set_minor_locator(matplotlib.ticker.LogLocator(base=10, subs=range(2, 10)))
ax.tick_params(which="minor", length=2, color=GRID)
ax.grid(axis="x", which="major", color=GRID, lw=0.7); ax.grid(axis="x", which="minor", color=GRID, lw=0.35, alpha=0.7)
ax.set_axisbelow(True)
for s_ in ("top", "right"): ax.spines[s_].set_visible(False)
ax.set_xlabel("Standard uncertainty (1 SD)")
ax.plot([], [], "o", color=MUTED, mfc="white", label="before: bias removed by a shift known in advance")
ax.plot([], [], "o", color=INK, label="after the per-recording correction (≤: upper bound)")
ax.plot([], [], "D", ms=3.5, color=INK, mfc="white", label="likely value (part shared with a second reference)")
ax.legend(loc="upper center", bbox_to_anchor=(0.4, -0.16), ncol=1, frameon=False, fontsize=6.5)
fig.subplots_adjust(left=0.4, right=0.97, top=0.98, bottom=0.27)
fig.savefig(sys.argv[3])
print(len(uniq), "forms as stored;", len(P), "corrected sources")
