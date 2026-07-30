# One-shot: create public GitHub repo and push (after `gh auth login`)

```powershell
cd C:\Users\markk\OneDrive\Documents\at-utility

# If not logged in:
#   gh auth login --hostname github.com --git-protocol https --web

gh repo create ohm --public --source=. --remote=origin --push

# Then set plugin repository to the printed URL, e.g.:
#   https://github.com/<your-username>/ohm
```

Use that URL as Cursor marketplace **global repo link**.
Logotype URLs after site deploy:

- `https://www.withohm.dev/ohm-icon.svg`
- `https://www.withohm.dev/ohm-icon-360.png`
- or relative `assets/logo.svg` in the repo
