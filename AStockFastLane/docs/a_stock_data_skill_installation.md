# a-stock-data Skill Installation Notes

## 1. Source

- Repository: https://github.com/simonlin1212/a-stock-data
- README checked: https://github.com/simonlin1212/a-stock-data/blob/main/README.md
- SKILL.md checked: https://github.com/simonlin1212/a-stock-data/blob/main/SKILL.md
- Checked time: 2026-06-14 01:07:43 +08:00

## 2. Installation Steps Attempted

1. Read local Codex `skill-installer` instructions.
2. Checked whether `C:\Users\Administrator\.codex\skills\a-stock-data` already existed.
3. Installed from GitHub with:

```bash
python C:\Users\Administrator\.codex\skills\.system\skill-installer\scripts\install-skill-from-github.py --repo simonlin1212/a-stock-data --path . --name a-stock-data
```

4. Verified installed files by listing the skill directory.
5. Read the installed `SKILL.md` front matter and capability description.
6. Checked required Python dependencies from README / SKILL.md.
7. Installed the required Python packages:

```bash
python -m pip install mootdx requests pandas stockstats
```

8. Verified that Python can import / locate the dependency packages.
9. Tried to query the Codex skill registry with `list-skills.py --format json`; that remote query failed with HTTP 403, so active registry recognition could not be confirmed from the listing command.

## 3. Installed Location

The Skill was installed to:

```text
C:\Users\Administrator\.codex\skills\a-stock-data
```

Observed installed files:

- `SKILL.md`
- `README.md`
- `LICENSE`
- `CHANGELOG.md`
- `assets/`
- `.github/`

The installed `SKILL.md` contains front matter:

```text
name: a-stock-data
origin: custom
version: 3.2.2
```

## 4. Dependencies

README / SKILL.md list these Python dependencies:

- `mootdx`
- `requests`
- `pandas`
- `stockstats`

Installed / verified versions:

- `mootdx`: 0.11.7
- `requests`: 2.34.2
- `pandas`: 3.0.3
- `stockstats`: 0.6.8

`requirements.txt` was not modified. Reason: these packages are Skill execution dependencies for the installed development assistant, not yet confirmed AStockFastLane runtime dependencies. The project should decide runtime dependencies only when adapters are implemented.

## 5. Verification

Verification results:

- Skill directory exists: yes.
- `SKILL.md` exists at the installed location: yes.
- Skill metadata can be read locally: yes.
- Capability description is readable: yes.
- Python dependencies can be located by the current Python interpreter: yes.
- Codex current-session activation: not fully confirmed. The Skill was installed after this conversation started, and Codex generally needs a restart to pick up newly installed skills in the active skill list.
- `list-skills.py --format json` remote registry check failed with HTTP 403, so it did not confirm registry visibility.

No real A-share data endpoint was requested during this installation verification task.

## 6. Problems

- `python -m pip install mootdx requests pandas stockstats` exceeded the command timeout, but a follow-up import/metadata check showed all four packages were installed and visible.
- `list-skills.py --format json` failed with `Error: Failed to fetch skills: HTTP 403`, so remote listing could not verify active registry status.
- Current Codex session cannot prove automatic activation until Codex is restarted and the active skill list is refreshed.

## 7. Conclusion

B. Skill installed but not verified.

