# Lighthouse audit

Run the production server in one terminal, then run `pnpm audit:lighthouse`
in another. The command audits the public home page with desktop Chrome and
writes the machine-readable result to `lighthouse-report.json` (ignored by
Git). Keep performance and accessibility at or above 85 before release.

Baseline audited locally on 2026-09-14 against the production home page:

- Performance: 99
- Accessibility: 95
