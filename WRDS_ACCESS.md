# Getting the WRDS data (Compustat, CRSP, Execucomp)

Several projects use data licensed from **Wharton Research Data Services (WRDS)** — Compustat,
CRSP, Execucomp, and the CRSP/Compustat Merged (CCM) link. That data is **not** in this
repository and **must not be posted publicly or shared** — it is licensed, and redistribution
violates the subscription (and can jeopardize the whole institution's WRDS access).

The right way to work with it is to pull it yourself, through your **own WRDS account** under
George Mason University's subscription.

## 1. Get a WRDS account (enrolled GMU students)
1. Go to **https://wrds-www.wharton.upenn.edu/** → *Register*.
2. Register with your **@gmu.edu** email and select **George Mason University** as your
   institution. Choose the "Student" class of account.
3. Your request is routed to GMU's WRDS administrator for approval. Approval can take a day or
   two. If you are not approved (e.g., the ASSIP registration is not yet reflected), **email me**
   and I will help get you sponsored under the subscription.

> You are an enrolled GMU student for the summer, so you are eligible — but eligibility to *use*
> WRDS does **not** let anyone repost the data. Always pull it into your own workspace; never
> upload a WRDS extract to a public repo, an open Drive link, or anywhere outside authorized GMU
> users.

## 2. Pull the data for your project
Each project's `code/00_*.py` (e.g. `00_pull.py`, `00_pull_warn.py`) is the pull script. It
connects to WRDS and writes the raw files into that project's `data/` folder. With the `wrds`
Python package installed (`pip install wrds`):

```bash
cd <project>/            # e.g. 03_clawbacks_ceo_risk
python code/00_pull.py   # prompts for your WRDS username/password the first time
```

`data/README.md` in each project lists exactly which WRDS libraries and fields it pulls, so you
can see what you are getting before you run it.

## 3. Reproduce the rest
Everything after the pull is public and already in the repo. Once the raw data is local:

```bash
python code/05_*.py      # build the analytical panel
python code/1*_*.py      # estimate; writes output/tables/*.csv
python code/*_tables_tex.py
cd paper && tectonic main.tex
```

If anything fails or WRDS access is holding you up, email me — don't stay stuck.
