"""Facts for the Metrology Atlas paper, generated from the VitalDB atlas file.

    python facts/make_facts.py [ATLAS_JSON] [--resolution VITALDB_RESOLUTION_REPO]

Writes facts/facts.yaml and facts/facts.tex. Without ATLAS_JSON the atlas file is built from the metrology-atlas
repository next to this one ($METROLOGY_ATLAS_DIR, default ../metrology-atlas). Every number in main.tex that
describes the dataset comes from here as \\fact{id}; an undefined fact prints a red ?? in the PDF. Each fact records
the atlas item it comes from. The only other source is vitaldb-resolution (Figure 1C's analyser weights), which the
atlas names as the value model of the laboratory variables; without --resolution those two facts are left undefined.

Kept literal in main.tex: the AI assistant's own words in Box 1 (they quote the atlas file it was given), the
illustrative values (a heart rate of 72, a haematocrit of 35%), clause numbers of the VIM and GUM, version numbers,
DOIs, and what VitalDB's documentation says (Table 4, middle column).
"""
import argparse
import datetime
import hashlib
import json
import math
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
ATLAS_DIR = Path(os.environ.get("METROLOGY_ATLAS_DIR", ROOT.parent / "metrology-atlas"))

facts = {}
WORDS = {2: "two", 3: "three", 4: "four", 5: "five", 6: "six", 7: "seven", 8: "eight", 9: "nine", 10: "ten",
         11: "eleven", 12: "twelve"}


def fact(fid, value, display, unit, source, definition, n=None, status="measured"):
    facts[fid] = {"value": value, "display": display, "unit": unit, "status": status, "source": source,
                  "definition": definition}
    if n is not None:
        facts[fid]["n"] = n


def num(x, nd=0, sign=False):
    """LaTeX display: thousands separators, a true minus, an explicit plus if asked."""
    s = f"{abs(x):,.{nd}f}"
    if x < 0:
        return f"$-${s}"
    return f"$+${s}" if sign else s


def word(n, cap=False):
    w = WORDS.get(n, str(n))
    return w.capitalize() if cap else w


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("atlas_json", nargs="?")
    ap.add_argument("--resolution")
    a = ap.parse_args()

    if a.atlas_json:
        path = Path(a.atlas_json)
    else:
        path = Path(tempfile.mkdtemp()) / "vitaldb.metrology.json"
        subprocess.run([sys.executable, "-m", "metrology_atlas", "json", "datasets/vitaldb", "--out", str(path)],
                       cwd=ATLAS_DIR, check=True, stdout=subprocess.DEVNULL)
    raw = path.read_bytes()
    J = json.loads(raw)
    # rev-parse and status only: `git describe --dirty` refreshes the index and takes index.lock, which a checkout
    # mounted from another machine may not be able to remove.
    def git(*args):
        return subprocess.run(["git", "--no-optional-locks", "-C", str(ATLAS_DIR), *args],
                              capture_output=True, text=True).stdout.strip()
    try:
        commit = git("rev-parse", "--short", "HEAD")
        if commit and git("status", "--porcelain", "--untracked-files=no"):
            commit += "-dirty"
    except OSError:
        commit = ""

    V, P, S = J["variables"], J["parameters"], J["studies"]

    def form(vid, fid):
        return next(t for t in V[vid]["timing"] if t["id"] == fid)

    def uc(vid, fid):
        return math.sqrt(sum(c["u_s"] ** 2 for c in form(vid, fid)["uncertainty"]["components"]))

    def comp(vid, fid, i):
        return form(vid, fid)["uncertainty"]["components"][i]

    # ---- the atlas as a whole
    src = "atlas file"
    for kind in ("variables", "clocks", "links", "devices", "parameters", "observations"):
        fact(f"atlas.{kind}", len(J[kind]), num(len(J[kind])), kind, f"{src}: {kind}", f"number of {kind}")
    fact("atlas.studies", len(S), num(len(S)), "studies", f"{src}: studies", "number of studies")
    cur = sum(s["status"] == "current" for s in S.values())
    fact("atlas.studies.current", cur, num(cur), "studies", f"{src}: studies[].status", "studies with status current")
    timed = [v for v in V.values() if v.get("timing")]
    nforms = sum(len(v["timing"]) for v in timed)
    fact("atlas.forms", nforms, num(nforms), "forms", f"{src}: variables[].timing", "timing forms")
    fact("atlas.timed", len(timed), num(len(timed)), "variables", f"{src}: variables[].timing",
         "variables with timing forms")
    oq = sum(len(x.get("open_questions") or []) for k in ("studies", "examples") for x in J[k].values())
    fact("atlas.open_questions", oq, num(oq), "questions", f"{src}: studies, examples open_questions",
         "open questions listed")
    kinds = [k for k in J if k not in ("schema", "dataset")]
    fact("atlas.kinds", len(kinds), word(len(kinds)), "kinds", f"{src}: top-level keys", "kinds of item")
    fact("atlas.methods", len(J["methods"]), word(len(J["methods"])), "methods", f"{src}: methods",
         "general methods")
    cases = J["dataset"]["records"]["max"]
    fact("vitaldb.cases", cases, num(cases), "cases", f"{src}: dataset.records.max", "cases in the release")

    # ---- BIS EEG
    b = form("bis-eeg", "bis-sync")["removes_bias_s"]
    fact("bis.bias", b["median"], num(b["median"], 2), "s", "bis-eeg/bis-sync removes_bias_s.median",
         "BIS EEG stamp minus the same burst on the working reference, median between recordings", b["n"])
    fact("bis.bias.exact", b["median"], num(b["median"], 3), "s", "bis-eeg/bis-sync removes_bias_s.median",
         "as bis.bias, to the millisecond")
    fact("bis.bias.early", -b["median"], num(-b["median"], 2), "s", "bis-eeg/bis-sync removes_bias_s.median",
         "how early the BIS EEG stamps sit (minus the bias)")
    fact("bis.bias.p5", b["p5"], num(b["p5"], 2), "s", "bis-eeg/bis-sync removes_bias_s.p5", "5th percentile")
    fact("bis.bias.p95", b["p95"], num(b["p95"], 2), "s", "bis-eeg/bis-sync removes_bias_s.p95", "95th percentile")
    fact("bis.bias.n", b["n"], num(b["n"]), "recordings", "bis-eeg/bis-sync removes_bias_s.n", "recordings")
    for fid, key in (("bis-sync", "sync"), ("bis-own", "own"), ("bis-shift", "shift")):
        u = uc("bis-eeg", fid) * 1000
        fact(f"bis.{key}.uc", u, num(u), "ms", f"bis-eeg/{fid} components (combined)",
             f"combined standard uncertainty, form {fid}")
    for i, key in enumerate(("recording", "drift", "grid")):
        c = comp("bis-eeg", "bis-sync", i)
        u = c["u_s"] * 1000
        fact(f"bis.sync.u.{key}", u, num(u, 1 if u < 10 else 0), "ms",
             f"bis-eeg/bis-sync uncertainty.components[{i}]", c["name"])
    L = comp("bis-eeg", "bis-sync", 1)["length_s"] / 60
    fact("bis.sync.length", L, num(L), "min", "bis-eeg/bis-sync uncertainty.components[1].length_s",
         "correlation length of the drift left by the stamp model")
    lo, hi = form("bis-eeg", "bis-sync")["uncertainty"]["interval95_s"]
    fact("bis.sync.i95.lo", lo, num(lo * 1000, sign=True), "ms", "bis-eeg/bis-sync interval95_s", "95% interval, lower")
    fact("bis.sync.i95.hi", hi, num(hi * 1000, sign=True), "ms", "bis-eeg/bis-sync interval95_s", "95% interval, upper")
    g = form("bis-eeg", "bis-sync")["grid_s"] * 1000
    fact("bis.grid", g, num(g, 1), "ms", "bis-eeg/bis-sync grid_s", "sample grid of the BIS EEG (1 / 128 Hz)")
    nf = len(V["bis-eeg"]["timing"])
    fact("bis.forms", nf, word(nf, cap=True), "forms", "bis-eeg timing", "timing forms of the BIS EEG")
    ns = len(form("bis-eeg", "bis-sync").get("studies") or [])
    fact("bis.sync.studies", ns, word(ns), "studies", "bis-eeg/bis-sync studies", "studies behind the form")
    n = P["stamp-model-error"]["spread"]["n"]
    fact("bis.sync.n", n, num(n), "recordings", "parameter stamp-model-error spread.n",
         "recordings with at least 5 good burst windows")
    step = next(t for t in J["devices"]["bis"]["tracks"] if t["track"] == "EEG1_WAV")["step"]
    fact("bis.eeg.step", float(step), step, "uV", "device bis tracks EEG1_WAV step", "value grid of the BIS EEG")

    # ---- Primus
    u = uc("primus-awp", "primus-shift")
    fact("primus.shift.uc", u, num(u, 2), "s", "primus-awp/primus-shift components (combined)",
         "combined standard uncertainty with a shift known in advance")
    u = uc("primus-awp", "primus-sync") * 1000
    fact("primus.sync.uc", u, num(u), "ms", "primus-awp/primus-sync components (combined)",
         "combined standard uncertainty after breath matching")
    n = form("primus-awp", "primus-sync")["removes_bias_s"]["n"]
    fact("primus.sync.n", n, num(n), "recordings", "primus-awp/primus-sync removes_bias_s.n",
         "recordings with breath matching (with CVP)")
    g = P["primus-numeric-gap"]["value"]
    fact("primus.numgap.half", g / 2, num(g / 2, 1), "s", "parameter primus-numeric-gap (half)",
         "half the median Primus numeric interval: the error of a phase drawn uniform over the gap")
    p = P["primus-awp-pause"]
    fact("primus.pause", p["value"], num(p["value"]), "s", "parameter primus-awp-pause", p["quantity"])
    fact("primus.pause.n", p["spread"]["n"], num(p["spread"]["n"]), "recordings", "parameter primus-awp-pause spread.n",
         "recordings with AWP pauses")
    p = P["primus-period"]
    fact("primus.period", p["value"], num(p["value"]), "s", "parameter primus-period", p["quantity"])
    gain = next(t for t in J["devices"]["primus"]["tracks"] if t["track"] == "CO2" and t.get("corrected_gain"))
    fact("primus.co2.gain", gain["corrected_gain"], f"{gain['corrected_gain']:g}", "mmHg/code",
         "device primus tracks CO2 corrected_gain", "corrected gain of the CO2 waveform")

    # ---- heart rate and ECG
    p = P["hr-truncation-share"]
    fact("hr.trunc.share", p["value"], num(p["value"], 1), "%", "parameter hr-truncation-share", p["quantity"])
    fact("hr.trunc.n", p["spread"]["n"], num(p["spread"]["n"]), "recordings", "parameter hr-truncation-share spread.n",
         "recordings")
    lo, hi = form("solar8000-hr", "hr-lab")["support_s"]
    fact("hr.support", [lo, hi], f"{lo:g}--{hi:g}", "s", "solar8000-hr/hr-lab support_s", "support of the HR")
    nlab = form("solar8000-hr", "hr-lab")["removes_bias_s"]["n"]
    fact("hr.lab.n", nlab, num(nlab), "recordings", "solar8000-hr/hr-lab removes_bias_s.n", "recordings with a label")
    ng = P["hr-delay-early"]["spread"]["n"] + P["hr-delay-late"]["spread"]["n"]
    fact("hr.groups.n", ng, num(ng), "recordings", "parameters hr-delay-early + hr-delay-late spread.n",
         "recordings assigned to a delay group")
    fact("hr.groups.none", nlab - ng, num(nlab - ng), "recordings", "hr.lab.n minus hr.groups.n",
         "labelled recordings not assigned to a group", status="derived")
    u = comp("solar8000-hr", "hr-lab", 0)["u_s"]
    fact("hr.label.u", u, num(u, 2), "s", "solar8000-hr/hr-lab uncertainty.components[0].u_s",
         "standard uncertainty of a recording's own delay label")
    w = comp("lab-blood-gas", "lab-draw", 0)["u_s"] * math.sqrt(12)
    fact("lab.access.width", w, num(w), "s", "lab-blood-gas/lab-draw components[0].u_s x sqrt(12)",
         "length of the arterial-line access the draw lies in (uniform)", status="derived")
    saw = comp("snuadc-ecg-ii", "snu-raw", 0)["u_s"] * math.sqrt(12) * 1000
    fact("ecg.sawtooth", saw, num(saw), "ms", "snuadc-ecg-ii/snu-raw components[0].u_s x sqrt(12)",
         "span of the stamp sawtooth (uniform)", status="derived")
    u = uc("snuadc-ecg-ii", "snu-model") * 1000
    fact("ecg.model.uc", u, num(u, 1), "ms", "snuadc-ecg-ii/snu-model components (combined)",
         "combined standard uncertainty after the stamp model")
    bits = {t.get("bits_to_store") for t in J["devices"]["snuadc"]["tracks"] if t.get("bits_to_store")}
    assert len(bits) == 1, bits
    nb = bits.pop()
    fact("snuadc.bits", nb, str(nb), "bits", "device snuadc tracks bits_to_store", "bits the SNUADC codes use")

    # ---- CO2 sampling line
    p = P["co2-sampling-line-lag"]
    fact("co2.line", p["value"], num(p["value"], 2), "s", "parameter co2-sampling-line-lag", p["quantity"])
    for k in ("q1", "q3", "n"):
        v = p["spread"][k]
        fact(f"co2.line.{k}", v, num(v, 0 if k == "n" else 2), "s" if k != "n" else "recordings",
             f"parameter co2-sampling-line-lag spread.{k}", k)

    # ---- mains hum and the working reference
    fact("pc.grid.multi", P["pc-grid-rate-multi"]["value"], num(P["pc-grid-rate-multi"]["value"], sign=True), "ppm",
         "parameter pc-grid-rate-multi", P["pc-grid-rate-multi"]["quantity"])
    fact("pc.grid.single", P["pc-grid-rate-single"]["value"], num(P["pc-grid-rate-single"]["value"], sign=True), "ppm",
         "parameter pc-grid-rate-single", P["pc-grid-rate-single"]["quantity"])
    s = P["pc-grid-rate-setups"]["spread"]
    fact("pc.grid.setups.min", s["min"], num(s["min"], sign=True), "ppm", "parameter pc-grid-rate-setups spread.min",
         "lowest setup median")
    fact("pc.grid.setups.max", s["max"], num(s["max"], sign=True), "ppm", "parameter pc-grid-rate-setups spread.max",
         "highest setup median")
    for fid, pid in (("snuadc.hum.share", "snuadc-hum-share"), ("snuadc.uncorr.share", "snuadc-uncorrected-share")):
        p = P[pid]
        sh = 100 * p["value"] / p["spread"]["n"]
        fact(fid, sh, num(sh), "%", f"parameter {pid} (value / spread.n)", p["quantity"], status="derived")
    p = P["snuadc-uncorrected-hum"]
    fact("snuadc.uncorr.hum", p["value"], num(p["value"]), "recordings", "parameter snuadc-uncorrected-hum",
         p["quantity"])
    for fid, pid in (("snuadc.drift", "snuadc-uncorrected-drift"), ("snuadc.drift.hum", "snuadc-uncorrected-drift-hum"),
                     ("snuadc.drift.hourly", "snuadc-uncorrected-drift-hourly"),
                     ("snuadc.drift.hum.hourly", "snuadc-uncorrected-drift-hum-hourly")):
        p = P[pid]
        fact(fid, p["value"], num(p["value"]), p["unit"], f"parameter {pid}", p["quantity"], p["spread"]["n"])
    n = P["snuadc-uncorrected-drift"]["spread"]["n"]
    fact("snuadc.drift.n", n, num(n), "recordings", "parameter snuadc-uncorrected-drift spread.n",
         "recordings in the BIS check")

    # ---- loop closure
    p = P["loop-bis-misclosure"]
    fact("loop.bis", p["value"], num(p["value"], 1, sign=True), "ppm", "parameter loop-bis-misclosure", p["quantity"])
    fact("loop.bis.n", p["spread"]["n"], num(p["spread"]["n"]), "loops", "parameter loop-bis-misclosure spread.n",
         "loops")
    p = P["loop-bis-z3-share"]
    fact("loop.bis.z3", p["value"], num(p["value"]), "%", "parameter loop-bis-z3-share", p["quantity"])
    s = P["loop-variance-factor"]["spread"]
    fact("loop.vf.min", s["min"], num(s["min"]), "", "parameter loop-variance-factor spread.min",
         "smallest variance factor")
    fact("loop.vf.max", s["max"], num(s["max"], 1), "", "parameter loop-variance-factor spread.max",
         "largest variance factor")
    fact("loop.se.min", math.sqrt(s["min"]), num(math.sqrt(s["min"]), 1), "",
         "sqrt of loop-variance-factor spread.min", "factor by which standard errors are too small", status="derived")
    fact("loop.se.max", math.sqrt(s["max"]), num(math.sqrt(s["max"]), 1), "",
         "sqrt of loop-variance-factor spread.max", "factor by which standard errors are too small", status="derived")

    # ---- documentation and data quality
    p = P["opend-imputed"]
    fact("opend.imputed", p["value"], num(p["value"]), "cases", "parameter opend-imputed", p["quantity"])
    sh = 100 * p["value"] / p["spread"]["n"]
    fact("opend.imputed.share", sh, num(sh, 1), "%", "parameter opend-imputed (value / spread.n)", "share of cases",
         status="derived")

    # ---- Figure 1C: analyser weights for a haematocrit of 35 (vitaldb-resolution, the atlas's value model)
    if a.resolution:
        sys.path.insert(0, str(Path(a.resolution).resolve()))
        import vitaldb_resolution as vr
        comps = {c["label"]: c for c in vr.load().distribution("hct", 35).to_dict()["components"]}
        for k, lab in (("bg", "blood_gas"), ("cbc", "cbc")):
            w = 100 * comps[lab]["weight"]
            fact(f"hct.weight.{k}", w, num(w), "%", f"vitaldb-resolution distribution('hct', 35) {lab}",
                 f"weight of the {lab} analyser for a recorded haematocrit of 35%")

    doc = {"generated": datetime.date.today().isoformat(),
           "atlas": {"file": str(path) if a.atlas_json else f"built from {ATLAS_DIR.name}", "sha256": hashlib.sha256(raw).hexdigest(), "commit": commit,
                     "schema": J.get("schema")},
           "facts": facts}
    (HERE / "facts.yaml").write_text(yaml.safe_dump(doc, sort_keys=False, allow_unicode=True), encoding="utf-8")
    tex = ["% generated by facts/make_facts.py; do not edit",
           f"% atlas {commit} sha256 {doc['atlas']['sha256'][:16]}",
           "\\makeatletter"]
    for fid, f in facts.items():
        disp = f["display"].replace(",", "{,}").replace("%", "\\%")
        tex.append(f"\\@namedef{{fact@{fid}}}{{{disp}}}")
    tex.append("\\makeatother")
    (HERE / "facts.tex").write_text("\n".join(tex) + "\n", encoding="utf-8")
    print(f"{len(facts)} facts from atlas {commit}")


if __name__ == "__main__":
    main()
