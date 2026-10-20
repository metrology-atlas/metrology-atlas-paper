"""Build the arXiv upload: arxiv/ (main.tex, main.bbl, the figures it uses), arxiv.tar.gz and abstract.txt.

    python make_arxiv.py            # refuses on \\todo{...}, TODO-style markers in the references or the PDF,
                                    # unresolved references, or a figure too large for its page
    python make_arxiv.py --draft    # builds anyway, for a test upload

Steps: build the paper with latexmk in a scratch copy (for main.bbl), collect the figures named by
\\includegraphics, compile the bundle on its own with pdflatex only (as arXiv does: no BibTeX), and write the
abstract as plain text for the arXiv form (limit 1,920 characters). Everything lands in arxiv/, which git ignores.
"""
import argparse
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "arxiv"
LIMIT = 1920


def run(cmd, cwd):
    r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    return r.returncode, r.stdout + r.stderr


def plain_abstract(tex):
    a = re.search(r"\\begin\{abstract\}(.*?)\\end\{abstract\}", tex, re.S).group(1)
    a = a.replace("\\,", " ").replace("~", " ").replace("---", "\u2014").replace("--", "\u2013")
    a = re.sub(r"\\(emph|textit|textbf)\{([^}]*)\}", r"\2", a)
    a = re.sub(r"\\url\{([^}]*)\}", r"\1", a)
    a = a.replace("\\%", "%").replace("\\&", "&")
    if "\\" in a or "{" in a:
        raise SystemExit("abstract still contains LaTeX: " + re.findall(r"\\\w+|\{", a)[0])
    return re.sub(r"\s+", " ", a).strip()


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--draft", action="store_true")
    a = ap.parse_args(argv)
    tex = (HERE / "main.tex").read_text(encoding="utf-8")
    body = tex.replace(r"\newcommand{\todo}", "")
    todos = re.findall(r"\\todo\{", body)
    problems = [f"{len(todos)} \\todo left in the text"] if todos else []
    with tempfile.TemporaryDirectory() as tmp:
        build = Path(tmp) / "build"
        shutil.copytree(HERE, build, ignore=shutil.ignore_patterns(".git", "arxiv", "arxiv.tar.gz", "*.pdf.tmp"))
        code, log = run(["latexmk", "-pdf", "-interaction=nonstopmode", "-halt-on-error", "main.tex"], build)
        if code:
            raise SystemExit("latexmk failed:\n" + log[-2000:])
        mlog = (build / "main.log").read_text(encoding="utf-8", errors="ignore")
        if re.search(r"(Reference|Citation) `[^']*' .*undefined", mlog):
            problems.append("undefined references or citations")
        if "Float too large" in mlog:
            problems.append("a figure is too large for its page (see main.log)")
        bbl = (build / "main.bbl").read_text(encoding="utf-8", errors="ignore")
        for marker in ("TODO", "TBD", "FIXME", "XXX"):
            if marker in bbl or marker in (build / "references.bib").read_text(encoding="utf-8", errors="ignore"):
                problems.append(f"{marker} in the references")
        code, text = run(["pdftotext", "main.pdf", "-"], build)
        if not code and re.search(r"\bTODO\b|\?\?|\bTBD\b|\bFIXME\b", text):
            problems.append("TODO, TBD, FIXME or ?? in the built PDF text")
        figs = sorted(set(re.findall(r"\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}", tex)))
        if OUT.exists():
            shutil.rmtree(OUT)
        (OUT / "figures").mkdir(parents=True)
        shutil.copy(build / "main.tex", OUT)
        shutil.copy(build / "main.bbl", OUT)
        for f in figs:
            src = build / (f if Path(f).suffix else f + ".pdf")
            shutil.copy(src, OUT / src.relative_to(build))
        # arXiv compiles with pdflatex only, from main.bbl: check the bundle does the same
        check = Path(tmp) / "check"
        shutil.copytree(OUT, check)
        for _ in range(3):
            code, log = run(["pdflatex", "-interaction=nonstopmode", "-halt-on-error", "main.tex"], check)
            if code:
                raise SystemExit("bundle does not compile on its own:\n" + log[-2000:])
        clog = (check / "main.log").read_text(encoding="utf-8", errors="ignore")
        if re.search(r"(Reference|Citation) `[^']*' .*undefined", clog):
            problems.append("bundle has undefined references or citations")
        pages = re.search(r"Output written on main.pdf \((\d+) pages?", clog).group(1)
        shutil.copy(check / "main.pdf", OUT / "main-arxiv-check.pdf")
    abstract = plain_abstract(tex)
    if len(abstract) > LIMIT:
        problems.append(f"abstract is {len(abstract)} characters (limit {LIMIT})")
    (OUT / "abstract.txt").write_text(abstract + "\n", encoding="utf-8")
    nfig = len(figs)
    (OUT / "comments.txt").write_text(
        f"{pages} pages, {nfig} figures; companion website https://vitaldb.metrology-atlas.org\n", encoding="utf-8")
    tar = HERE / "arxiv" / "arxiv.tar.gz"
    with tarfile.open(tar, "w:gz") as t:
        for p in sorted(OUT.rglob("*")):
            if p.is_file() and p.name not in ("abstract.txt", "comments.txt", "arxiv.tar.gz", "main-arxiv-check.pdf"):
                t.add(p, arcname=str(p.relative_to(OUT)))
    print(f"bundle: {tar.relative_to(HERE)} ({tar.stat().st_size // 1024} KB; main.tex, main.bbl, {nfig} figures)")
    print(f"compiles on its own: {pages} pages (arxiv/main-arxiv-check.pdf)")
    print(f"abstract: {len(abstract)} of {LIMIT} characters (arxiv/abstract.txt)")
    print(f"comments: {(OUT / 'comments.txt').read_text().strip()}")
    for p in problems:
        print("NOT READY:", p)
    return 1 if problems and not a.draft else 0


if __name__ == "__main__":
    sys.exit(main())
