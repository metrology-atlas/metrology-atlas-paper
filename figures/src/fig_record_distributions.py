"""Figure 1: one recorded pair as a joint distribution over its true time and true value, from the atlas's own data.

    python figures/src/fig_record_distributions.py ATLAS_JSON LABELS_DIR RESOLUTION_REPO figures/fig1-record-distributions.pdf

ATLAS_JSON: the atlas file (python -m metrology_atlas json datasets/vitaldb --out ...). LABELS_DIR: the vitaldb-bench
label tables (numeric_delay_labels.csv, lab_draw_labels.csv). RESOLUTION_REPO: the vitaldb-resolution repository.
Nothing here is drawn as a Gaussian unless the source says so; empirical distributions are smoothed with a narrow kernel.
Panel C is shaded on a square-root scale so that the thin central-lab line shows.

Each panel: grey, before correction (what the stored record alone allows, release-wide); blue, after correction
(what the atlas gives for one typical record). Superseded description of the old single-layer figure follows.

A. Monitor heart rate recorded as 72 (Solar8000): the value is truncated (atlas value block), so the true value is
   uniform on [72, 73). The value describes a 6-10 s window of ECG (its support, from the timing form), which closes a
   delay d before the stamp; d is the per-recording delay label across the release (two groups of recording PCs).
B. One SNUADC ECG sample: on the raw stamps the true time is 0-480 ms before the stamp, uniform over the sawtooth
   (snu-raw form); the value is one 10-bit code (0.00987 mV, uniform). After the stamp model the time is known to 1.6 ms.
C. A haematocrit of 35 % in the lab table: which analyser made it is not recorded. Blood gas (integer, 77 %) or the
   central laboratory (0.1, 23 %), from vitaldb-resolution; the draw precedes the lab stamp by that analyser's delay,
   from the lab-draw labels. Value and time are a mixture of the two, and they go together.
"""
import json
import sys
from pathlib import Path

import matplotlib
import numpy as np
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.colors import LinearSegmentedColormap  # noqa: E402

INK, MUTED, GRID, BLUE, ORANGE = "#1b2333", "#5a6170", "#e4e3df", "#2a78d6", "#eb6834"
CMAP = LinearSegmentedColormap.from_list("b", ["#ffffff", "#cfe0f6", "#7fb0ea", BLUE, "#174a8b"])
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 7.5, "axes.edgecolor": MUTED,
                     "xtick.color": MUTED, "ytick.color": MUTED, "axes.labelcolor": INK})
ECG_STEP_MV = 0.00987          # SNUADC ECG code step (atlas study track-value-resolution)


def kde(samples, x, bw):
    s = np.asarray(samples, float)[:, None]
    k = np.exp(-0.5 * ((x[None, :] - s) / bw) ** 2).sum(0)
    return k / (k.sum() * (x[1] - x[0]))


def uniform(x, a, b):
    u = ((x >= a) & (x < b)).astype(float)
    return u / (u.sum() * (x[1] - x[0]))


def style(ax):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.tick_params(length=2.5, labelsize=7)


def joint(ax, x, y, z, extent):
    ax.imshow(z / z.max(), origin="lower", extent=extent, aspect="auto", cmap=CMAP, vmin=0, vmax=1,
              interpolation="nearest")


def marg_top(ax, x, p, col=BLUE):
    ax.fill_between(x, p / p.max(), color=col, alpha=0.25, lw=0, step=None)
    ax.plot(x, p / p.max(), color=col, lw=1.0)
    ax.set_ylim(0, 1.15); ax.axis("off")


def marg_right(ax, y, p, col=BLUE):
    ax.fill_betweenx(y, p / p.max(), color=col, alpha=0.25, lw=0)
    ax.plot(p / p.max(), y, color=col, lw=1.0)
    ax.set_xlim(0, 1.15); ax.axis("off")


def panel(fig, box, t, v, pt, pv, z=None, sqrt=False):
    """Joint PDF with its two marginals; box = (left, right, bottom, top) in figure fractions."""
    g = fig.add_gridspec(2, 2, width_ratios=[4.2, 0.55], height_ratios=[0.55, 3.2], left=box[0], right=box[1],
                         bottom=box[2], top=box[3], wspace=0.04, hspace=0.05)
    ax = fig.add_subplot(g[1, 0]); axt = fig.add_subplot(g[0, 0], sharex=ax); axv = fig.add_subplot(g[1, 1], sharey=ax)
    zz = np.outer(pv, pt) if z is None else z
    joint(ax, t, v, zz ** 0.5 if sqrt else zz, (t[0], t[-1], v[0], v[-1]))
    marg_top(axt, t, pt); marg_right(axv, v, pv)
    ax.set_xlim(t[0], t[-1]); ax.set_ylim(v[0], v[-1]); style(ax)
    ax.grid(True, color="#d9d8d3", lw=0.5, alpha=0.7); ax.set_axisbelow(False)
    return ax, axt


def main(atlas_json, labels_dir, resolution_repo, out):
    """Top: before correction, what the stored record alone allows (release-wide). Bottom: after correction, what
    the atlas gives for one typical record (medians of the per-record labels)."""
    J = json.load(open(atlas_json))
    V = J["variables"] if isinstance(J["variables"], dict) else {v["id"]: v for v in J["variables"]}
    hr = V["solar8000-hr"]; bg = V["lab-blood-gas"]
    sup_lo, sup_hi = next(t for t in hr["timing"] if t["id"] == "hr-lab")["support_s"]
    step = hr["value"]["step"]; assert hr["value"]["anchor"] == "floor"
    draw = next(t for t in bg["timing"] if t["id"] == "lab-draw")
    draw_w = draw["uncertainty"]["components"][0]["u_s"] * np.sqrt(12) / 60   # where in the line access, min (uniform)
    labels = Path(labels_dir)
    nd = pd.read_csv(labels / "numeric_delay_labels.csv")
    hrl = nd[nd.track == "Solar8000/HR"].dropna(subset=["delay_from_window_end_s"])
    d_hr = hrl.delay_from_window_end_s.values
    d_one = float(np.median(d_hr[d_hr > 3.0]))                           # a typical record in the larger (late) group
    se_one = float(hrl.se_s.median()); win_one = float(hrl.window_s.median())
    ld = pd.read_csv(labels / "lab_draw_labels.csv")
    lag_bg = ld[ld.panel == "blood_gas"].lag_s.dropna().values / 60
    lag_cb = ld[ld.panel == "central"].lag_s.dropna().values / 60
    lag_one = float(np.median(lag_bg))                                    # a typical blood-gas draw, min
    sys.path.insert(0, str(resolution_repo))
    import vitaldb_resolution as vr
    comps = {c["label"]: c for c in vr.load().distribution("hct", 35).to_dict()["components"]}
    w_bg, w_cb = comps["blood_gas"]["weight"], comps["cbc"]["weight"]

    fig = plt.figure(figsize=(7.0, 5.0))
    L, R = (0.08, 0.50), (0.60, 0.985)
    TOP, BOT = (0.555, 0.905), (0.075, 0.425)
    t = np.linspace(-16, 1.5, 3501); v = np.linspace(70.6, 74.4, 761); pv = uniform(v, 72, 72 + step)
    tc = np.linspace(-32, 1.5, 3351); vc = np.linspace(34.2, 35.8, 801)

    def hr_marks(ax, close, lo, hi, note):
        ax.plot(0, 72, "o", ms=5, mfc="white", mec=INK, mew=1.3, zorder=5)
        ax.axvline(0, color=MUTED, lw=0.6, ls=(0, (3, 3)))
        yb = 73.7
        ax.plot([close - lo, close], [yb, yb], color=ORANGE, lw=2.2, solid_capstyle="butt")
        if hi > lo:
            ax.plot([close - hi, close - lo], [yb, yb], color=ORANGE, lw=2.2, ls=(0, (1.5, 1.2)))
        ax.plot([close, close], [yb - 0.12, yb + 0.12], color=ORANGE, lw=1.4)
        ax.text(close - hi, yb + 0.2, note, fontsize=6.3, color=ORANGE, va="bottom")
        ax.text(-15.6, 72.5, "rounded down: equally likely\nanywhere from 72 up to 73", fontsize=6.3, color=BLUE, va="center")
        ax.set_ylabel("true heart rate (bpm)"); ax.set_xticks(np.arange(-16, 1, 2)); ax.set_yticks([71, 72, 73, 74])

    # A: heart rate, before
    ax, axt = panel(fig, (*L, *TOP), t, v, kde(-d_hr, t, 0.12), pv)
    hr_marks(ax, -np.median(d_hr), sup_lo, sup_hi, f"its support: {sup_lo:g}–{sup_hi:g} s of ECG, shown at the median delay")
    axt.text(-1.0, 0.8, "two groups of\nrecording PCs", fontsize=6.2, color=MUTED, ha="left")
    ax.annotate("recorded pair\n(stamp, 72 bpm)", (0, 72), (-3.0, 71.0), fontsize=6.5, color=INK, ha="right",
                arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.7))
    # C: heart rate, after
    ax, axt = panel(fig, (*L, *BOT), t, v, np.exp(-0.5 * ((t + d_one) / se_one) ** 2), pv)
    hr_marks(ax, -d_one, win_one, win_one, f"its support: this recording's {win_one:g} s of ECG")
    axt.text(-d_one + 0.5, 0.8, f"this recording's delay,\n±{se_one:.2f} s", fontsize=6.2, color=MUTED, ha="left")
    ax.set_xlabel("true time of the window's close, relative to the stamp (s)")

    # B: haematocrit, before
    pt_bg, pt_cb = kde(-lag_bg, tc, 0.35), kde(-lag_cb, tc, 0.6)
    pv_bg = uniform(vc, comps["blood_gas"]["lower"], comps["blood_gas"]["upper"])
    pv_cb = uniform(vc, comps["cbc"]["lower"], comps["cbc"]["upper"])
    z = w_bg * np.outer(pv_bg, pt_bg) + w_cb * np.outer(pv_cb, pt_cb)
    ax, axt = panel(fig, (*R, *TOP), tc, vc, w_bg * pt_bg + w_cb * pt_cb, w_bg * pv_bg + w_cb * pv_cb, z=z, sqrt=True)
    ax.plot(0, 35, "o", ms=5, mfc="white", mec=INK, mew=1.3, zorder=5)
    ax.text(-31, 35.62, f"wide band: blood gas, whole % ({w_bg:.0%})", fontsize=6.2, color=INK)
    ax.text(-31, 35.12, f"thin line: central lab, 0.1 % ({w_cb:.0%})", fontsize=6.2, color=INK)
    ax.set_ylabel("Hct (%)")
    axt.text(-31, 0.6, "either analyser's turnaround", fontsize=6.2, color=MUTED, ha="left")
    # D: haematocrit, after
    pt_a = uniform(tc, -lag_one - draw_w / 2, -lag_one + draw_w / 2)
    ax, axt = panel(fig, (*R, *BOT), tc, vc, pt_a, pv_bg)
    ax.plot(0, 35, "o", ms=5, mfc="white", mec=INK, mew=1.3, zorder=5)
    ax.text(-31, 35.62, "blood gas (named by the draw's label), whole %", fontsize=6.2, color=INK)
    axt.text(-lag_one - 1.2, 0.5, f"drawn within this arterial-line\naccess (about {draw_w * 60:.0f} s)", fontsize=6.2, color=MUTED, ha="right")
    ax.set_ylabel("Hct (%)"); ax.set_xlabel("time of the draw relative to the lab stamp (min)")

    fig.text(0.012, 0.965, "Monitor heart rate", fontsize=9, fontweight="bold", color=INK)
    fig.text(0.53, 0.965, "Laboratory haematocrit", fontsize=9, fontweight="bold", color=INK)
    for y, lab in ((0.935, "Before correction: what the stored record alone allows"),
                   (0.455, "After correction: what the atlas gives for this one record")):
        fig.text(0.5, y, lab, fontsize=7.6, color=MUTED, ha="center", style="italic")
    for x, y, k in ((0.012, 0.905, "A"), (0.53, 0.905, "B"), (0.012, 0.425, "C"), (0.53, 0.425, "D")):
        fig.text(x, y, k, fontsize=9, fontweight="bold", color=INK)
    fig.savefig(out, facecolor="white")
    fig.savefig(str(out)[:-4] + "_preview.png", dpi=200, facecolor="white")


if __name__ == "__main__":
    main(*sys.argv[1:5])
