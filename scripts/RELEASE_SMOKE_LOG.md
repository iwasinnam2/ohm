# Release smoke log (Section A)

| Date (UTC) | Result | Host | Notes |
|------------|--------|------|-------|
| 2026-07-29 | RELEASE_SMOKE_OK | local compose :8080/:8081 | Fixed rust health match + emdash parse; OpenAI miss/hit green |

GO_LIVE asks for three consecutive days. Re-run:

```powershell
.\scripts\release_smoke.ps1
```

Append a row each green day before Section C cutover.
