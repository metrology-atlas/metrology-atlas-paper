# Supplementary material: an AI assistant answering a planning question from the atlas file

## Set-up (29 October 2026)

- **Input:** the atlas file alone, `vitaldb.metrology.json` (1.08 MB), built from the atlas repository with
  `python -m metrology_atlas json datasets/vitaldb`. No website, no paper, no other context.
- **Assistant:** a fresh Claude agent (model configured as claude-opus-5-5), with file and Python tools and no web
  access. It read the file's schema, explored it with Python (11 tool calls, about 100 s), and answered.
- **Instruction:** answer the researcher in plain language, 400–700 words; name the atlas item behind each claim;
  say which numbers are measured and which estimated or assumed; say where the atlas is silent; end with what to do.
- **The answer below is verbatim.** It was then checked claim by claim against the atlas (table at the end).

## The researcher's question

> I'm planning to use signals ECG, BIS EEG and ETCO2 from VitalDB, and I have made these assumptions about
> synchronisation and uncertainty: the three signals are synchronised to within 50 ms as stored, and their timing
> uncertainties are independent of each other. What does the atlas tell me about my assumptions, and how might they
> affect my research?

## The answer (verbatim)

**Short answer:** neither assumption holds as stated. As stored, the three signals are out of step by hundreds of
milliseconds to several seconds, not 50 ms. Their timing errors are not independent of each other, and within each
signal they are not independent over time either.

**1. "Synchronised to within 50 ms as stored"**

- **ECG** (`snuadc-ecg-ii`, form `snu-raw`): the raw stamps run ahead of the true time by a median of 0.24 s (p5–p95
  0.01–0.47 s). This is a sawtooth that builds up to about 480 ms and is pulled back about every 2.08 h. Standard
  uncertainty is 139 ms. Measured.
- **BIS EEG** (`bis-eeg`, form `bis-raw`): for the same burst seen in both signals, the EEG stamp sits a median
  −787 ms from the ECG stamp (p5–p95 −970 to −601 ms, 2,702 recordings). On top of that come 113 ms between
  recordings and 114 ms of drift within a recording. Measured. The `look_ahead` note says raw stamps put the EEG
  0.6–1.0 s ahead of the event it shows.
- **ETCO2** (`primus-numerics`, form `primus-num`): each value describes the last completed breath. It is stamped a
  median 1.55 s after that breath (parameter `etco2-delay`, p10–p90 0.75–3.4 s, measured). The spread between
  recordings is 2.4 s.
    - The Primus clock is a separate problem. It drifts +104 ppm, about 0.4 s per hour (parameter
      `primus-drift-breath`, measured), and wanders a median 1.5 s over a recording (link `primus-vs-pc`).
    - The gas sampling line adds a further 3.6 s (study `co2-sampling-line`, measured).
    - The atlas gives no single ETCO2-to-ECG figure. It also contradicts itself on the ETCO2 delay. `etco2-delay`
      gives +1.55 s, but study `numerics-derivation-release` reports −2.05 s measured against the CO2 waveform, and
      form `primus-lab` says its labels are measured against that waveform. The atlas does not resolve this.

**Even after correction, only ECG–EEG gets close to 50 ms:**

- **ECG–EEG with the mode constant** (form `bis-sync`): median absolute error 42 ms, standard uncertainty 62 ms
  (stated as an upper bound), 95% interval −233 to +166 ms. Parameter `stamp-model-error`, measured.
- **ECG–EEG with the recording's own bursts** (form `bis-own`): standard uncertainty 30 ms, 95% interval −116 to
  +150 ms.
- **Wrong correction mode:** applying one EEG–ECG constant to every recording is about 110 ms wrong in the
  frequent-correction minority (observation `eeg-ecg-offset-by-mode`).
- **Long uncorrected recordings:** in recordings where the ECG clock is never corrected, the reference itself can
  drift about 76 ms per hour (form `snu-model` evidence; observation `snuadc-long-uncorrected`). The 1.5 ms residual
  for the ECG is estimated, not measured.
- **CO2 after breath matching** (`primus-co2`, form `primus-sync`): median error 55 ms, 95% −262 to +272 ms, but
  only in the 1,067 recordings that have CVP. The 3.6 s sampling-line delay remains after this correction, with
  0.25 s spread between recordings.
- **ETCO2 after the per-case label** (`primus-lab`): label uncertainty 0.21 s. That form lists no Primus clock
  component, and the atlas does not say whether one is needed.
- **ETCO2 timing is coarse by nature:** each value describes a whole breath (window 3–30 s), so a 50 ms target is not
  meaningful for it.

**2. "Timing uncertainties are independent"**

- **Shared reference:** both corrections measure against the ECG's converter (SNUADC). The BIS offset is measured
  against the corrected ECG (`bis-eeg` bias evidence), and the Primus is aligned to the CVP channel, which shares the
  ECG's clock (observation `snuadc-one-clock`). So the corrected EEG and ETCO2 errors are defined relative to the
  ECG. Any error in the reference itself is common to all three. The `reference` entry under `dataset.domains` says
  drift "cancels between them": it is positively correlated in absolute time and cancels in differences.
- **Shared keys within a device:** `shared_with` links errors that move together. Within the ECG it is "SNUADC
  clock"; within the Primus signals it is "Primus clock" and "Primus breath matching" (the latter shared with airway
  pressure).
- **Errors persist over time:**
    - The BIS error has an exponential correlation length of 8 min (`bis-sync`); uncorrected, it is roughly constant
      over each 8,192 s correction cycle (`bis-raw`).
    - The Primus breath-matching error has a correlation length of 7 min.
    - Components with scope "recording" are constant for a whole recording, so averaging windows within a patient
      does not shrink them.
- **Unknown structure:** a few components have scope "unknown" and status "estimated": the ECG stamp-model residual,
  and the 0.3 s drift within a stretch in `primus-shift`.
- **What the atlas does not say:** it gives no correlation coefficient between the BIS and Primus device-clock
  errors, and no shared key connects them. Their independence beyond the shared reference is plausible but not
  stated.

**How this could affect your research**

- **Lags and ordering:** raw-stamp analyses of lags between EEG, ECG and CO2 would be biased by about 0.8 s (EEG) and
  by several seconds (ETCO2), and could reverse which change appears first.
- **Coupling measures:** ECG–EEG coherence or coupling at sub-second scales would be smeared.
- **Confidence intervals:** treating errors as independent across signals and windows would make them too narrow,
  because recording-level and slowly varying errors do not average out.
- **Atlas maturity:** the atlas is a pre-release (v0.1.0, October 2026, `dataset.notice`), and some numbers rest on
  small studies.

**What to do**

1. Treat the corrected ECG time (`snu-model`) as your reference. Use `bis-own` where a recording has at least 5 good
   burst windows; otherwise use `bis-sync` with that recording's mode constant.
2. Shift ETCO2 back by its per-case delay label, and treat each value as describing one breath with uncertainty
   measured in seconds. If you need breath-level timing, use the CO2 waveform after breath matching and subtract the
   3.6 s sampling line. This is only possible where CVP exists.
3. Propagate the uncertainty with the atlas's correlation structure: resample by recording, and in blocks of at least
   8 min within a recording. Run sensitivity analyses at the 95% bounds.
4. Ask the atlas maintainers to settle the ETCO2 delay contradiction (1.55 s versus −2.05 s), and report in your
   methods which timing forms you used.

## Verification against the atlas

| Claim | Atlas item | Verdict |
|---|---|---|
| ECG raw stamps: 0.24 s median, 0.01–0.47 s, sawtooth to 480 ms every 2.08 h, u 139 ms | `snuadc-ecg-ii` / `snu-raw` | Correct |
| BIS raw: −787 ms (−970 to −601), 2,702 recordings; 113 and 114 ms components; look-ahead 0.6–1.0 s | `bis-eeg` / `bis-raw` | Correct |
| ETCO2 stamped 1.55 s after the breath (0.75–3.4 s) | parameter `etco2-delay` | Correct |
| Primus drift +104 ppm | parameter `primus-drift-breath` | Correct |
| Primus lag moves a median 1.5 s over a recording | a study page, not link `primus-vs-pc` | Number correct; item misattributed |
| Sampling line 3.6 s, spread 0.25 s | study `co2-sampling-line`; `primus-co2` / `primus-sync` | Correct |
| ETCO2 labels and release fit contradict each other (+1.55 against −2.05 s) | `etco2-delay`; `numerics-derivation-release` | Correct, and a real conflict in the atlas (traced to the fit's phase model and corrected) |
| ECG–EEG after correction: 42 ms median, u 62 ms upper bound, 95% −233 to +166 ms; own bursts 30 ms | `bis-sync`, `bis-own`, parameter `stamp-model-error` | Correct |
| One constant for all modes about 110 ms wrong in frequent mode | observation `eeg-ecg-offset-by-mode` | The assistant's inference (−804 against −660 ms); not stated as such |
| Uncorrected reference drifts about 76 ms per hour | `snu-model` evidence; study `hum-snuadc-rate` | Correct |
| CO2 after breath matching: 55 ms, 95% −262 to +272 ms, 1,067 recordings | `primus-co2` / `primus-sync`; study text | Correct (the form's median absolute error is 53 ms; 55 ms is the study's window median) |
| `primus-lab` has no Primus clock component | `primus-numerics` / `primus-lab` | Correct, and it pointed to a real error: the numerics' forms were in the wrong clock domain (fixed) |
| Errors share the SNUADC reference; correlation lengths 8 and 7 min; recording-scope components | forms' `shared_with`, `length_s`, `scope`; `dataset.domains` | Correct |
| No stated correlation between BIS and Primus clock errors | — | Correct: the atlas is silent |
| Pre-release v0.1.0 | `dataset.notice` | Correct for the file tested; to update at release |

**Result.** Every number traces to the atlas. One citation points to the wrong item, and one figure is the
assistant's own inference, labelled as a claim. The exchange also found four problems in the atlas, now fixed or
recorded:

1. The ETCO2 delay conflict. Resolved: the release fit let each last-breath value have been computed anywhere in the
   7 s poll gap, which counts the hold twice and puts the delay about half a gap (3.5 s) too low. Per recording the
   labels sit 3.55 s above the fit (6,186 recordings), against a half gap of 3.51 s. The study page now carries the
   correction, and the same fix explains most of PEEP's negative delay.
2. Stale wording, "the EEG lags the ECG by −804 ms", from before the BIS sign was settled (fixed in
   `eeg-ecg-offset-by-mode` and `snuadc-stamp-sawtooth`).
3. No Primus clock term in the ETCO2 per-case-label form. Resolved: the Primus numerics are stamped by the recorder
   PC on arrival, so the Primus clock does not enter their stamps; the real error was that their forms (and the
   Solar8000 numerics' forms) sat in a device's clock domain. They now sit in a recorder-PC domain with no drift.
4. The release notice still said v0.1.0 (updated to v0.2.0).
