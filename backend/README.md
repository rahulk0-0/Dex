# Hosted DEX processing for mobile and PC

Live application: https://dex-editor-lite.onrender.com

Source: https://github.com/rahulk0-0/Dex

The Render Docker service runs genuine DEX assembly/disassembly for mobile and PC. The original static editor at https://dex-editor-lite-rahul.nutmegatlas.chatgpt.site is also configured to use this backend. The static host itself cannot execute Java.

## Deploy on Render

The repository includes a root Dockerfile and render.yaml. Deploy the repository as a Docker web service. The image builds the React frontend and installs Python, Gunicorn, Flask, Java 17 and the pinned Smali jars. It serves both the editor and DEX endpoints at the same HTTPS origin. No PC companion is needed for that hosted URL.

Use a repository accessible to your Render account. A live service has been provisioned from this repository; see the URL above. Source files alone do not provision another service. The source repository attached to the static site is authenticated separately; connect a Git provider or supply an accessible source repository during deployment.

The included blueprint requests a free instance; actual availability and limits are controlled by the hosting provider. No paid plan has been selected or purchased. Free hosting may suspend idle services; the first conversion or health check can take longer during startup.

## Existing editor connection

After the service is live, update public/dex-config.json in the static editor to `{"apiBase":"https://ACTUAL-DEPLOYED-HOST"}` and rebuild/publish. Alternatively, open DEX processing in the editor, select Hosted server, paste the actual HTTPS origin and save/test. The setting is local to that browser. The full editor hosted by the Docker image discovers its own origin through /dex-config.json without configuration.

Do not use 127.0.0.1 from a phone to reach a PC. Local companion mode is for processing on the same computer.

## Runtime settings

- PORT: hosting-assigned listen port, defaults to 10000.
- ALLOWED_ORIGINS: comma-separated browser origins. Defaults to the existing editor's HTTPS origin. Render's RENDER_EXTERNAL_URL is also allowed for its same-origin frontend.
- DEX_WEB_ROOT: compiled frontend directory; /app/web in Docker.
- DEX_MAX_HEAP_MB: Java heap per conversion; 320 in hosted container, 768 for local companion by default.
- DEX_CONCURRENCY: 1 hosted conversion at once, 2 for local companion by default.
- MAX_REQUEST_MB: 32 MiB hosted JSON request limit. Base64 and JSON overhead count, so a binary DEX must be smaller than roughly 24 MiB. Large inputs or Smali sets may need a larger hosting instance and adjusted limits.

## Behavior and privacy

DEX bytes and Smali assembled into DEX are uploaded to the selected hosting service. This replaces the previous browser/local-only DEX path. Search, editing, and text/ZIP export remain in the browser. Conversion inputs/outputs use per-request temporary directories and are removed on normal completion or failure. A killed process or machine crash may leave temporary files until the ephemeral host is recycled. No database or permanent upload folder is used.

The application disables access logging and adds no telemetry. Hosting-provider operational logs are outside the application's control. There is no application login or API credential; the service is publicly reachable, with an origin allowlist, bounded requests and a one-operation gate. The origin allowlist is a browser control, not authentication. Do not treat the public API as a private network service.

- POST /disassemble: {"data":"BASE64_DEX"} → {"files":[{"name":"...smali","text":"..."}],"api":28}
- POST /assemble: {"files":[{"name":"...smali","text":"..."}],"api":28} → {"data":"BASE64_DEX","classes":1}
- GET /health: toolchain readiness information and request limit.
- GET /dex-config.json: same-origin frontend configuration.

Invalid DEX, invalid Smali, duplicate classes, oversize requests and processing errors return JSON errors; no fake DEX is returned. Standard DEX 035/037/038/039 only. A valid DEX structure does not establish that modified app behavior is correct on a device.

## Verification

`python3 -m pip install -r backend/requirements.txt`

`python3 -m unittest discover -s tests -v`

`npm ci && npm run build`

Docker image builds require a Docker-capable host. The shared conversion code and HTTP adapter are covered by nine local tests. Live HTTPS import/edit/export/reimport and an actual browser DEX import, replacement, export and downloaded-file validation were also verified. A physical mobile browser was not separately tested.
