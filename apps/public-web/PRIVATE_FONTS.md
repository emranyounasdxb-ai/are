# Owner-controlled font runtime

Commercial webfont files are **not distributed through Git, CI, Docker images,
artifacts or source maps**. Purchase documents stay in the owner's private records.
The website necessarily serves the licensed webfonts to visitors; public runtime
font URLs are not a DRM mechanism and do not disclose the private storage location.

Provision the seven immutable files in the ignored `.private-fonts/` directory
inside this workspace. `lib/private-font-manifest.mjs` defines logical filenames,
checksums, families, genuine weight ranges and required EN/AR glyph coverage. Never
copy certificates into that directory. An absolute location may instead be supplied
at runtime through `ARE_PRIVATE_FONT_DIR`; never commit its owner-specific value.

`npm run fonts:check --workspace=@are/public-web` validates the exact original bytes
before development, production builds and startup. The Node instrumentation gate
also protects direct Next startup. Asset requests repeat validation and fail closed.
Hennigar Italic's original malformed Windows name is accepted only with its pinned
hash, intact Macintosh full-name record, weight/style and glyph verification.

Fonts are self-hosted at versioned `/font-assets/v1/` routes; localized layouts
preload critical faces. A font update requires an approved new checksum/contract
and URL version bump. Actual ranges are Auren 100–800 and Aeternus 100–856; do not
invent weights. Arabic body remains the OFL IBM Plex Sans Arabic package. Its
licence is retained under `public/fonts/licenses/`.

Local Docker builds use the seven files as required read-only BuildKit secrets,
not copied build inputs. Do not export build caches containing unrelated private
materials. The running Public container mounts only that directory read-only and
validates before listening. Run the optional web services with:

```powershell
docker compose -f compose.yaml -f compose.web.yaml build public-web admin-web
docker compose -f compose.yaml -f compose.web.yaml up -d --no-deps public-web admin-web
```

This does not migrate data or restart PostgreSQL, Redis or the API. Production uses
the same owner-provisioned read-only mechanism; this document does not authorize
deployment. Missing, altered or invalid fonts stop runtime startup. Metric-adjusted
system faces are only brief loading/error fallbacks, never silent approval to ship
different production typography.

GitHub CI has no fonts, credentials or private retrieval. Only an explicit **build**
with both `CI=true` and `ARE_FONT_BUILD_MODE=code-only` can skip commercial validation.
This mode cannot start a runtime and must not be represented as visual/font proof.
CI uses the open-source Arabic font as its decoder regression fixture. Owner-local
actual-font builds and EN/AR desktop/mobile checks are a separate release gate.
