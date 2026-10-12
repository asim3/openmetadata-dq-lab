# ui-checks

Maintainer scripts that drive the OpenMetadata UI with Playwright for Python, to check the learning path against what the screens show. Not for participants.

- Install into the repo venv: `pip install -r ui-checks/requirements.txt`. Do not run `playwright install`: the scripts use the Chrome already on the host (`channel="chrome"`).
- Run from the repo root, for example `python ui-checks/item13_f.py`. They log in as the lab admin, read database credentials from `.env`, and save screenshots to the git-ignored `Screenshots/`.
- `g1_f.py` and the scripts that log in as the steward user need `STEWARD_PW` in the environment (the password of a throwaway lab account you create yourself). Never commit it.
- The scripts are exploratory: several were edited in place while finding locators, so expect to adjust them. `common.py` (login, screenshots) and `dq.py` (create a test case) are the reusable parts.
