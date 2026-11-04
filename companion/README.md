# DEX Editor Lite — local companion

This bundle contains the complete browser editor and pinned Smali/Baksmali 2.5.2 Java tools. No third-party conversion service is used. No runtime downloads are needed.

## Start on Windows
1. Install **Java 11 or later** and **Python 3.10 or later**, if not already installed. Confirm `java -version` and `python --version` in a terminal.
2. Unzip this entire folder.
3. Double-click **start.bat**, or run `python server.py` from the extracted folder.
4. Open **http://127.0.0.1:8787** in your browser.
5. Open a DEX, edit its disassembled classes, then Export → select the DEX group.

On macOS/Linux run `python3 server.py` instead. Stop with Ctrl+C. The service only binds 127.0.0.1. Keep the terminal open during use.

## What works where
- Browser: Smali/TXT/XML imports, syntax highlighting, editor undo/redo, class/method/field navigation, all-file find and replace, replacement previews, text and ZIP downloads.
- Local Java companion: DEX disassembly, assembly, checksum/signature verification, re-disassembly validation. All classes in the chosen import group are included, including unmodified classes.
- Hosted editor: can connect to the companion if the browser permits local-network requests. If the browser blocks this, use the local URL above. It includes the same interface and requires no hosted account.

## Limits
- Standard DEX 035, 037, 038 and 039. DEX 040/041, Compact DEX, ODEX and APK packages are unsupported and rejected.
- 80 MiB DEX import, 16 MiB per text file, 150 MiB JSON request, 180-second conversion timeout, two simultaneous Java processes.
- Local temporary processing uses disk and up to 768 MiB Java heap per operation. Temporary directories are removed on normal completion or errors; an OS/process crash may leave temporary files.
- The disassembler preserves classes and semantic metadata supported by its toolchain, not byte-for-byte layout. Original bytes remain untouched. A valid DEX structure does not prove that edited code behaves correctly on an Android device.
- Workspace edits live in memory. Export before closing. The app asks the browser to warn on leaving with unsaved edits.
- Ctrl/Cmd F: find; Ctrl/Cmd H: replace; Ctrl/Cmd S: export menu; Ctrl/Cmd O: open; Ctrl/Cmd Z: undo; Ctrl Y / Cmd Shift Z: redo.
- Regex uses JavaScript Unicode expressions, supports $1 captures, $&, $$ and named captures in replacements. Search runs in a cancellable worker with a 5-second timeout and a 100,000-match limit per file. First 10,000 matches per active file are highlighted. Preview shows the first 30 changes per file; all counted changes are applied.
- Replacements can be undone in each file's editor history. The notification's “Undo all” also restores the workspace snapshot from immediately before the replacement; use it before making further unrelated edits.
- ZIP exports contain every current text/Smali file, grouped by import. DEX exports operate on one import group at a time. Plain Smali files share the Loose files group; duplicate class declarations are rejected.
- XML means UTF-8 textual XML, not Android compiled binary XML.

## Rebuilding the web editor
The source repository uses React, TypeScript, Vite, Tailwind, CodeMirror 6 and JSZip. Run `npm ci` then `npm run build`. Copy the built dist directory to companion/web, excluding the downloadable companion ZIP itself, before creating the companion ZIP.

## Toolchain
Bundled JARs are pinned in setup.py, downloaded from Maven Central, and compared with published SHA-1 checksums during setup. This is an integrity check against transport errors, not an independent authenticity proof. To regenerate missing jars, run `python setup.py` with internet access before using the app. User documents are never passed to setup.py.

Smali project: https://github.com/JesusFreke/smali
Java runtime must be installed separately; it is not included in this download.

## Mobile and hosted mode

The updated editor also offers Hosted server in DEX processing. On mobile, use a deployed HTTPS backend; the PC companion cannot run on the phone. The hosted backend source and Docker/Render configuration are in backend/, Dockerfile and render.yaml in the full project. The connection is not active until a real backend is deployed and configured. Hosted mode uploads DEX/Smali conversion input to that backend.
