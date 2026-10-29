"""Figure 1: one recorded pair as a joint distribution over its true time and true value, from the atlas's own data.

    python figures/src/fig_record_distributions.py ATLAS_JSON LABELS_DIR RESOLUTION_REPO figures/fig1-record-distributions.pdf

ATLAS_JSON: the atlas file (python -m metrology_atlas json datasets/vitaldb --out ...). LABELS_DIR: the vitaldb-bench
label tables (numeric_delay_labels.csv, lab_draw_labels.csv). RESOLUTION_REPO: the vitaldb-resolution repository.
Nothing here is drawn as a Gaussian unless the source says so; empirical distributions are smoothed with a narrow kernel.
Panel C is shaded on a square-root scale so that the thin central-lab line shows.

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


def main(atlas_json, labels_dir, resolution_repo, out):
    J = json.load(open(atlas_json))
    V = J["variables"] if isinstance(J["variables"], dict) else {v["id"]: v for v in J["variables"]}
    hr = V["solar8000-hr"]; ecg = V["snuadc-ecg-ii"]
    form = next(t for t in hr["timing"] if t["id"] == "hr-lab")
    sup_lo, sup_hi = form["support_s"]
    step = hr["value"]["step"]; assert hr["value"]["anchor"] == "floor"
    raw = next(t for t in ecg["timing"] if t["id"] == "snu-raw")
    saw = raw["uncertainty"]["components"][0]["u_s"] * np.sqrt(12)       # sawtooth amplitude, s (uniform)
    model = next(t for t in ecg["timing"] if t["id"] == "snu-model")
    u_model = np.sqrt(sum(c["u_s"] ** 2 for c in model["uncertainty"]["components"]))
    labels = Path(labels_dir)
    nd = pd.read_csv(labels / "numeric_delay_labels.csv")
    d_hr = nd[nd.track == "Solar8000/HR"].delay_from_window_end_s.dropna().values
    ld = pd.read_csv(labels / "lab_draw_labels.csv")
    lag_bg = ld[ld.panel == "blood_gas"].lag_s.dropna().values / 60
    lag_cb = ld[ld.panel == "central"].lag_s.dropna().values / 60
    sys.path.insert(0, str(resolution_repo))
    import vitaldb_resolution as vr
    reg = vr.load()
    comps = {c["label"]: c for c in reg.distribution("hct", 35).to_dict()["components"]}

    fig = plt.figure(figsize=(7.0, 3.7))
    # ---------------- A ----------------
    gs = fig.add_gridspec(2, 2, width_ratios=[4.2, 0.6], height_ratios=[0.7, 4.2], left=0.07, right=0.56,
                          bottom=0.12, top=0.86, wspace=0.04, hspace=0.05)
    ax = fig.add_subplot(gs[1, 0]); axt = fig.add_subplot(gs[0, 0], sharex=ax); axv = fig.add_subplot(gs[1, 1], sharey=ax)
    t = np.linspace(-16, 1.5, 1751); v = np.linspace(70.6, 74.4, 761)
    pt = kde(-d_hr, t, 0.12); pv = uniform(v, 72, 72 + step)
    joint(ax, t, v, np.outer(pv, pt), (t[0], t[-1], v[0], v[-1]))
    ax.plot(0, 72, "o", ms=5.5, mfc="white", mec=INK, mew=1.4, zorder=5)
    ax.axvline(0, color=MUTED, lw=0.6, ls=(0, (3, 3)))
    ax.annotate("recorded pair\n(stamp, 72 /min)", (0, 72), (-3.2, 70.95), fontsize=6.8, color=INK, ha="right",
                arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.7))
    close = -np.median(d_hr); yb = 73.65
    ax.plot([close - sup_lo, close], [yb, yb], color=ORANGE, lw=2.2, solid_capstyle="butt")
    ax.plot([close - sup_hi, close - sup_lo], [yb, yb], color=ORANGE, lw=2.2, ls=(0, (1.5, 1.2)))
    ax.plot([close, close], [yb - 0.12, yb + 0.12], color=ORANGE, lw=1.4)
    ax.text(close - sup_hi, yb + 0.2, f"the {sup_lo:g}–{sup_hi:g} s of ECG it describes (its support), shown closing at the median",
            fontsize=6.4, color=ORANGE, va="bottom")
    ax.text(-15.6, 72.5, "truncated: true value\nuniform on [72, 73)", fontsize=6.6, color=BLUE, va="center")
    ax.set_xlim(t[0], t[-1]); ax.set_ylim(v[0], v[-1])
    ax.set_xlabel("true time of the window's close, relative to the stamp (s)")
    ax.set_ylabel("true heart rate (/min)"); style(ax)
    marg_top(axt, t, pt)
    axt.text(-np.percentile(d_hr, 80), 1.12, "two groups of recording PCs", fontsize=6.4, color=MUTED, ha="center", va="bottom")
    marg_right(axv, v, pv)
    fig.text(0.012, 0.955, f"A   Monitor heart rate  ({len(d_hr):,} recordings)", fontsize=8.5, fontweight="bold", color=INK)

    # ---------------- B ----------------
    gB = fig.add_gridspec(2, 2, width_ratios=[4, 0.6], height_ratios=[0.6, 3], left=0.66, right=0.985,
                          bottom=0.60, top=0.86, wspace=0.05, hspace=0.06)
    b = fig.add_subplot(gB[1, 0]); bt = fig.add_subplot(gB[0, 0], sharex=b); bv = fig.add_subplot(gB[1, 1], sharey=b)
    tb = np.linspace(-560, 60, 1241); vb = np.linspace(0.97, 1.03, 601)
    ptb = uniform(tb, -saw * 1000, 0); pvb = uniform(vb, 1.0 - ECG_STEP_MV / 2, 1.0 + ECG_STEP_MV / 2)
    joint(b, tb, vb, np.outer(pvb, ptb), (tb[0], tb[-1], vb[0], vb[-1]))
    b.plot(0, 1.0, "o", ms=4.5, mfc="white", mec=INK, mew=1.2, zorder=5)
    b.text(-545, 1.021, f"after the stamp model: ±{u_model * 1000:.1f} ms", fontsize=6.4, color=ORANGE)
    b.set_xlabel("true time relative to the stamp (ms)", labelpad=1); b.set_ylabel("ECG (mV)"); style(b)
    marg_top(bt, tb, ptb); marg_right(bv, vb, pvb)
    fig.text(0.62, 0.955, "B   ECG sample, raw stamps", fontsize=8.5, fontweight="bold", color=INK)

    # ---------------- C ----------------
    gC = fig.add_gridspec(2, 2, width_ratios=[4, 0.6], height_ratios=[0.6, 3], left=0.66, right=0.985,
                          bottom=0.12, top=0.38, wspace=0.05, hspace=0.06)
    c = fig.add_subplot(gC[1, 0]); ct = fig.add_subplot(gC[0, 0], sharex=c); cv = fig.add_subplot(gC[1, 1], sharey=c)
    tc = np.linspace(-32, 1.5, 1341); vc = np.linspace(34.2, 35.8, 801)
    w_bg, w_cb = comps["blood_gas"]["weight"], comps["cbc"]["weight"]
    pt_bg, pt_cb = kde(-lag_bg, tc, 0.35), kde(-lag_cb, tc, 0.6)
    pv_bg = uniform(vc, comps["blood_gas"]["lower"], comps["blood_gas"]["upper"])
    pv_cb = uniform(vc, comps["cbc"]["lower"], comps["cbc"]["upper"])
    z = w_bg * np.outer(pv_bg, pt_bg) + w_cb * np.outer(pv_cb, pt_cb)
    joint(c, tc, vc, z ** 0.5, (tc[0], tc[-1], vc[0], vc[-1]))
    c.plot(0, 35, "o", ms=4.5, mfc="white", mec=INK, mew=1.2, zorder=5)
    c.text(-31, 35.62, f"wide band: blood gas, whole % ({w_bg:.0%})", fontsize=6.2, color=INK)
    c.text(-31, 35.12, f"thin line: central lab, 0.1 % ({w_cb:.0%})", fontsize=6.2, color=INK)
    c.set_xlabel("time of the draw relative to the lab stamp (min)", labelpad=1); c.set_ylabel("Hct (%)"); style(c)
    pt = w_bg * pt_bg + w_cb * pt_cb; marg_top(ct, tc, pt)
    pvm = w_bg * pv_bg + w_cb * pv_cb; marg_right(cv, vc, pvm)
    fig.text(0.62, 0.47, "C   Lab haematocrit, source unknown", fontsize=8.5, fontweight="bold", color=INK)
    fig.savefig(out, facecolor="white")
    fig.savefig(str(out)[:-4] + "_preview.png", dpi=200, facecolor="white")


if __name__ == "__main__":
    main(*sys.argv[1:5])
