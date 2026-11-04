# DEX Editor Lite

React + TypeScript + Vite + Tailwind + CodeMirror 6, with a loopback Python/Java companion for genuine DEX conversion.

Run `npm ci` and `npm run dev` for the frontend. Run `python3 companion/server.py` for the DEX API. `npm run build` performs TypeScript checks and creates dist. Production hosting is static; Java cannot execute in the hosting platform's Worker runtime. The downloadable companion bundles the production frontend and JARs so the entire workflow runs on the user's computer.

See companion/README.md for setup, privacy, limitations, supported DEX versions and shortcuts.

Validation: `python3 -m unittest discover -s tests -v` checks genuine DEX round trips, preservation of unmodified classes, variable-length string edits, malformed instructions, duplicate classes and corrupt checksums.

No analytics, application login, database, remote conversion, or user-file persistence. The default hosted site audience is owner-private; the hosting access gate is separate from application functionality.

## Hosted mode for phones and PCs

See backend/README.md. The root Dockerfile and render.yaml package a real Java-backed service plus the editor. The frontend's DEX processing panel supports an HTTPS hosted endpoint or the optional local PC companion. Until an actual endpoint is deployed and configured, mobile DEX conversion is unavailable and reports that explicitly instead of trying localhost. Smali/TXT/XML functionality remains browser-based.

## Live deployment

Open https://dex-editor-lite.onrender.com on mobile or PC. Hosted DEX conversion needs no locally installed Python or Java. Source is published at https://github.com/rahulk0-0/Dex. The original private static editor also points to this backend. The free Render instance can sleep when idle; startup may take longer.
