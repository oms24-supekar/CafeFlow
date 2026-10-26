# CafeFlow — Behavioral reverse-engineering notes

We are documenting **observable interaction patterns** in kiosk ordering software, not bypassing controls or extracting proprietary assets/source code.

| Observed pattern to study | Our independent implementation | Validation |
|---|---|---|
| Category navigation | Category pills | Switching category filters menu |
| Product selection | Item cards and add button | Added line appears in cart |
| Quantity adjustment | +/- controls | Recomputed totals match prices |
| Clear checkout progression | Cart summary and checkout button | Empty cart cannot be checked out |
| Order token | Server-issued ID token | Each successful order gets a unique token |
| Receipt | Printable HTML | Receipt matches persisted order |
| Kitchen queue | Staff board | New order appears with status |

## Ethical and legal boundary
Use public UI references, your own test notes and software you are authorized to examine. Do not copy logos, imagery, branded layouts pixel-for-pixel, credentials, copyrighted code, or private APIs.

## Why the reverse-engineering-skill repository is optional
The skill at https://github.com/juank115/reverse-engineerskill describes binary/firmware/program triage and analysis. CafeFlow's first step is functional decomposition of observable UX, so no binary analysis is required.
