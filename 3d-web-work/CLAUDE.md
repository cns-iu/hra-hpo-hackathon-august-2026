# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repo layout

This is a hackathon repo with two mostly-independent parts:

- `3d-web-work/` — an Angular + BabylonJS web app that visualizes Human Reference Atlas (HRA) 3D organ models and lets a user manipulate/color scene nodes.
- `hpo-uberon-terms/data/` — source CSV data mapping HPO (Human Phenotype Ontology) terms to HRA digital objects, used as input to preprocessing.

There is no root-level build; each part is developed independently.

## Commands (`3d-web-work/`)

All commands run from `3d-web-work/`:

- `npm start` / `ng serve` — dev server at `http://localhost:4200/`, auto-reloads on change.
- `npm run build` / `ng build` — production build to `dist/`.
- `npm run watch` — development-config build in watch mode.
- `npm test` / `ng test` — run the Vitest unit test suite.
- `ng generate component <name>` — scaffold a new component (Angular CLI 22, standalone components).

### Preprocessing script (`3d-web-work/preprocessing/`)

`preprocess_hpo_hra.py` converts the HPO-HRA CSV into JSON for the viewer. Requires `pandas` (see `requirements.txt`).

```bash
python preprocessing/preprocess_hpo_hra.py
```

- Default input: `hpo-uberon-terms/data/hpo-hra-relevant-dos.csv` (HPO term IRI/label → cell type → HRA digital object type/URL).
- Default output dir: `3d-web-work/public/data/` (intended outputs: `hpo_hra_terms.json` flat list, `hpo_hra_by_do.json` grouped by digital object) — **not yet implemented**; the script currently only loads and pprints the dataframe.
- Both paths are overridable via `--input` / `--output-dir`.

## Architecture (`3d-web-work/`)

Standalone Angular app (no NgModules), bootstrapped from `src/main.ts` via `app.config.ts` (providers: `provideHttpClient`, `provideBrowserGlobalErrorListeners`).

- `App` (`src/app/app.ts`) is the root component. It toggles between two visualization approaches via a `showBabylon` signal, and separately fetches a sample kidney PURL JSON payload on init (currently just logged, not wired to either scene).
- `BabylonScene` (`src/app/components/babylon-scene/`) — renders a BabylonJS `Engine`/`Scene` directly onto a `<canvas>`. Loads a kidney `.glb` mesh from the Human Atlas CDN (`cdn.humanatlas.io/digital-objects/...`) via `ImportMeshAsync`, positions/scales it next to a reference box, and exposes methods (`changeKidneyColor`, `onToggle`) for manipulating the loaded mesh's `PBRMaterial`. This is the "raw BabylonJS" rendering path.
- `BodyUiScene` (`src/app/components/body-ui-scene/`) — wraps the `hra-body-ui` web component (hence `CUSTOM_ELEMENTS_SCHEMA`). Fetches a reference organ scene graph from the Human Atlas API (`apps.humanatlas.io/api/v1/reference-organ-scene`) as a list of `SceneNode` objects (each with optional `scenegraph` glTF URL, `color`, `opacity`), and mutates that array (recoloring, opacity, listing mesh names inside referenced `.glb` files by reading their glTF JSON chunk directly). This is the "declarative scene graph" rendering path, kept as a signal so the web component re-renders on mutation.

Both scene components pull live data from `humanatlas.io` endpoints/CDN at runtime — there are no local fixtures for organ geometry.

## Data (`hpo-uberon-terms/`)

`hpo-uberon-terms/data/hpo-hra-relevant-dos.csv` columns: `hpo_iri, hpo_label, term (cell type IRI), term_label, do_type (e.g. 2d-ftu), digital_object (HRA purl), file_url (asset URL, e.g. .svg/.glb on cdn.humanatlas.io)`. This is the join between phenotype terms and the digital objects renderable in `3d-web-work`.
