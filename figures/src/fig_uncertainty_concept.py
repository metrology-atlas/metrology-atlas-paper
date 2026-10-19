"""Conceptual figure: one record as a joint distribution over its true time and true value (illustrative numbers).

    python figures/src/fig_uncertainty_concept.py figures/fig0-uncertainty.pdf

A. A monitor heart rate stamped at t = 0 with value 72: it describes a 6 s window that ended 1.05-2.3 s before the
   stamp, and the monitor truncates, so the true value lies in [72, 73) blurred by its measurement error.
B. An ECG sample: milliseconds and microvolts, a tight, nearly symmetric spot.
C. A charted urine volume of 100 mL entered on a 5-minute mark: minutes wide, and heaped, so the true volume is
   skewed and broad (63-129 mL).
Shapes follow the atlas's models; widths are illustrative, not fitted.
"""
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.colors import LinearSegmentedColormap  # noqa: E402

INK, MUTED, GRID, BLUE, ORANGE = "#1b2333", "#5a6170", "#e4e3df", "#2a78d6", "#eb6834"
CMAP = LinearSegmentedColormap.from_list("b", ["#ffffff", "#cfe0f6", "#7fb0ea", BLUE, "#174a8b"])
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 7.5, "axes.edgecolor": MUTED,
                     "xtick.color": MUTED, "ytick.color": MUTED, "axes.labelcolor": INK})


def gauss(x, s):
    g = np.exp(-0.5 * (x / s) ** 2)
    return g / g.sum()


def conv(p, k):
    q = np.convolve(p, k, mode="same")
    return q / q.sum()


def uniform(x, a, b):
    return ((x >= a) & (x < b)).astype(float)


def joint(ax, x, px, y, py, extent):
    z = np.outer(py, px)
    ax.imshow(z / z.max(), origin="lower", extent=extent, aspect="auto", cmap=CMAP, vmin=0, vmax=1,
              interpolation="bilinear")


def style(ax):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.tick_params(length=2.5, labelsize=7)


def main(out):
    fig = plt.figure(figsize=(7.0, 3.55))
    gs = fig.add_gridspec(2, 2, width_ratios=[4.2, 0.75], height_ratios=[0.75, 4.2],
                          left=0.07, right=0.655, bottom=0.12, top=0.89, wspace=0.05, hspace=0.06)
    gr = fig.add_gridspec(2, 1, left=0.77, right=0.985, bottom=0.12, top=0.89, hspace=0.9)
    ax = fig.add_subplot(gs[1, 0])
    axt = fig.add_subplot(gs[0, 0], sharex=ax)
    axv = fig.add_subplot(gs[1, 1], sharey=ax)

    # A: heart rate
    t = np.linspace(-11, 2, 1301)
    dt = t[1] - t[0]
    end = uniform(t, -2.3, -1.05)                                  # where the window ends (delay behind the stamp)
    win = np.zeros_like(t)
    for e, w in zip(t, end):
        if w:
            win += uniform(t, e - 6, e)
    px = conv(win / win.sum(), gauss(np.arange(-0.2, 0.2 + dt, dt), 0.03))
    v = np.linspace(68.5, 76.5, 801)
    dv = v[1] - v[0]
    pv = conv(uniform(v, 72, 73), gauss(np.arange(-3, 3 + dv, dv), 0.6))
    joint(ax, t, px, v, pv, (t[0], t[-1], v[0], v[-1]))
    ax.plot(0, 72, "o", ms=5.5, mfc="white", mec=INK, mew=1.4, zorder=5)
    ax.annotate("recorded pair\n(stamp, 72 bpm)", (0, 72), (0.2, 75.3), fontsize=7, color=INK,
                arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.7), ha="left")
    ax.axvline(0, color=MUTED, lw=0.6, ls=(0, (3, 3)))
    ax.axhspan(72, 73, xmin=0, xmax=1, color=ORANGE, alpha=0.08, lw=0)
    ax.text(-10.7, 74.3, "the monitor truncates, so the\ntrue value lies in the band [72, 73)", va="bottom", fontsize=6.8,
            color=ORANGE)
    ax.annotate("", (-8.3, 69.3), (-1.05, 69.3), arrowprops=dict(arrowstyle="<->", color=MUTED, lw=0.7))
    ax.text(-4.7, 69.0, "a 6 s window of ECG, wherever it ends", ha="center", va="top", fontsize=6.8, color=MUTED)
    ax.annotate("", (-2.3, 70.3), (-1.05, 70.3), arrowprops=dict(arrowstyle="<->", color=MUTED, lw=0.7))
    ax.text(-1.7, 70.55, "window ends\n1.05–2.3 s\nbefore the stamp", ha="center", va="bottom", fontsize=6.6,
            color=MUTED)
    ax.set_xlim(-11, 2)
    ax.set_ylim(68.5, 76.5)
    ax.set_xlabel("true time relative to the stamp (s)")
    ax.set_ylabel("true heart rate (bpm)")
    style(ax)
    axt.fill_between(t, px / px.max(), color=BLUE, alpha=0.25, lw=0)
    axt.plot(t, px / px.max(), color=BLUE, lw=1.1)
    fig.text(0.012, 0.955, "A   Monitor heart rate", fontsize=8.5, fontweight="bold", color=INK, va="bottom")
    axt.axis("off")
    mv = pv / pv.max() > 0.003
    axv.fill_betweenx(v, pv / pv.max(), color=BLUE, alpha=0.25, lw=0)
    axv.plot((pv / pv.max())[mv], v[mv], color=BLUE, lw=1.1)
    axv.axis("off")

    # B: ECG sample (ms, mV)
    b = fig.add_subplot(gr[0])
    tb = np.linspace(-12, 12, 481)
    vb = np.linspace(0.90, 1.10, 401)
    joint(b, tb, gauss(tb, 3.0), vb, gauss(vb - 1.0, 0.012), (tb[0], tb[-1], vb[0], vb[-1]))
    b.plot(0, 1.0, "o", ms=4.5, mfc="white", mec=INK, mew=1.2)
    fig.text(0.70, 0.955, "B   ECG sample", fontsize=8.5, fontweight="bold", color=INK, va="bottom")
    b.set_xlabel("time (ms)", labelpad=1)
    b.set_ylabel("ECG (mV)")
    style(b)

    # C: charted urine volume (min, mL)
    c = fig.add_subplot(gr[1])
    tc = np.linspace(-12, 4, 641)
    dtc = tc[1] - tc[0]
    ptc = conv(uniform(tc, -5, 0), gauss(np.arange(-6, 6 + dtc, dtc), 1.5))
    vc = np.linspace(40, 160, 601)
    pvc = 0.55 * np.exp(-0.5 * ((vc - 95) / 14) ** 2) + 0.45 * np.exp(-0.5 * ((vc - 110) / 9) ** 2)
    pvc *= (vc > 60) & (vc < 132)
    pvc = conv(pvc / pvc.sum(), gauss(np.arange(-10, 10.2, 0.2), 2))
    joint(c, tc, ptc, vc, pvc, (tc[0], tc[-1], vc[0], vc[-1]))
    c.plot(0, 100, "o", ms=4.5, mfc="white", mec=INK, mew=1.2)
    fig.text(0.70, 0.47, "C   Charted volume", fontsize=8.5, fontweight="bold", color=INK, va="bottom")
    c.set_xlabel("time relative to the entry (min)", labelpad=1)
    c.set_ylabel("volume (mL)")
    style(c)
    fig.savefig(out, facecolor="white")
    if out.endswith(".pdf"):
        fig.savefig(out[:-4] + "_preview.png", dpi=200, facecolor="white")


if __name__ == "__main__":
    main(sys.argv[1])
