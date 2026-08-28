import { HttpClient } from '@angular/common/http';
import { Component, CUSTOM_ELEMENTS_SCHEMA, inject, signal } from '@angular/core';
import { firstValueFrom } from 'rxjs';

const organIri = '0000059';
const REFERENCE_ORGAN_SCENE_URL =
  'https://apps.humanatlas.io/api/v1/reference-organ-scene?organ-iri=http%3A%2F%2Fpurl.obolibrary.org%2Fobo%2FUBERON_'+ organIri + '&sex=male';

const HPO_HRA_CSV_URL = 'data/hpo-hra-relevant-dos.csv';

/** Minimal shape of the nodes the hra-body-ui `scene` array holds; only the fields we read/write are typed. */
interface SceneNode {
  color?: [number, number, number, number];
  scenegraph?: string;
  [key: string]: unknown;
}

/** One row of hpo-hra-relevant-dos.csv (hpo_iri, hpo_label, term, term_label, do_type, digital_object, file_url). */
interface HpoHraRow {
  hpo_iri: string;
  hpo_label: string;
  term: string;
  term_label: string;
  do_type: string;
  digital_object: string;
  file_url: string;
}

/** Parses a CSV with no quoted/escaped fields into an array of row objects keyed by header. */
function parseCsv(text: string): HpoHraRow[] {
  const [headerLine, ...lines] = text.trim().split('\n');
  const headers = headerLine.split(',');
  return lines
    .filter((line) => line.length > 0)
    .map(
      (line) =>
        Object.fromEntries(
          headers.map((header, i) => [header, line.split(',')[i]]),
        ) as unknown as HpoHraRow,
    );
}

/** One entry of a glTF file's `nodes[]` array; only the fields we read are typed. */
interface GlbNode {
  name?: string;
  extras?: {
    ontologyid?: string;
    representation_of?: string;
  };
}

/** Minimal shape of a parsed glTF file's JSON chunk; only the fields we read are typed. */
interface GlbJson {
  meshes?: { name: string }[];
  nodes?: GlbNode[];
}

/** Fetches a `.glb` file and parses its JSON chunk (glTF binary layout: 12-byte header, then chunks). */
async function fetchGlbJson(url: string): Promise<GlbJson> {
  const buf = await fetch(url).then((r) => r.arrayBuffer());
  const dv = new DataView(buf);
  const jsonLength = dv.getUint32(12, true);
  return JSON.parse(new TextDecoder().decode(new Uint8Array(buf, 20, jsonLength)));
}

/** Reads mesh names and each node's UBERON id/IRI (from `extras`) out of a `.glb` file. */
async function getGlbMeshInfo(
  url: string,
): Promise<{ meshNames: string[]; uberonIds: string[]; uberonIris: string[] }> {
  const json = await fetchGlbJson(url);
  const meshNames = (json.meshes ?? []).map((mesh) => mesh.name);
  const uberonIds = (json.nodes ?? [])
    .map((node) => node.extras?.ontologyid)
    .filter((id): id is string => typeof id === 'string');
  const uberonIris = (json.nodes ?? [])
    .map((node) => node.extras?.representation_of)
    .filter((iri): iri is string => typeof iri === 'string');
  return { meshNames, uberonIds, uberonIris };
}

@Component({
  selector: 'app-body-ui-scene',
  imports: [],
  templateUrl: './body-ui-scene.html',
  styleUrl: './body-ui-scene.css',
  schemas: [CUSTOM_ELEMENTS_SCHEMA],
})
export class BodyUiScene {
  private readonly http = inject(HttpClient);
  private originalSceneNodes: SceneNode[] = [];

  protected readonly sceneNodes = signal<SceneNode[]>([]);
  protected readonly hpoHraRows = signal<HpoHraRow[]>([]);

  constructor() {
    this.http.get<SceneNode[]>(REFERENCE_ORGAN_SCENE_URL).subscribe((nodes) => {
      this.originalSceneNodes = nodes.filter((node) => node.scenegraph !== undefined);
      this.sceneNodes.set(this.originalSceneNodes);
    });
  }

  /**
   * Adds one extra `scenegraphNode`-scoped scene entry per internal anatomical structure whose
   * UBERON IRI matches a `term` in the HPO-HRA CSV, colored yellow — the base organ entries are
   * left untouched, since `hra-body-ui` only colors a whole `.glb` unless a `scenegraphNode` is
   * given to scope an entry to one named node within it.
   */
  protected async ColorByHpoAssociation(): Promise<void> {
    if (this.hpoHraRows().length === 0) {
      await this.loadHpoHraCsv();
    }
    await this.highlightMatchingStructures(this.hpoHraRows());
  }

  protected uriToCurie(uri:string): string { 
    return uri
      .split("/").pop()?.replace("_",":") as string;
  }

  private async highlightMatchingStructures(rows: HpoHraRow[]): Promise<void> {
    const csvUberonIris = new Set(rows.map((row) => row.term).filter((iri) => iri.includes('UBERON')));

    const highlightNodes: SceneNode[] = [];
    for (const baseNode of this.originalSceneNodes) {
      if (!baseNode.scenegraph) continue;

      const json = await fetchGlbJson(baseNode.scenegraph);
      for (const glbNode of json.nodes ?? []) {
        const iri = glbNode.extras?.representation_of;
        if (glbNode.name && iri && csvUberonIris.has(iri)) {
          highlightNodes.push({
            ...baseNode,
            '@id': `${baseNode.scenegraph}#${glbNode.name}`,
            scenegraphNode: glbNode.name,
            color: [255, 0, 0, 250],
          });
        }
      }
    }
//
    this.sceneNodes.set([...this.originalSceneNodes, ...highlightNodes]);
  }

  protected resetColors(): void {
    this.sceneNodes.set(this.originalSceneNodes);
  }

  /**
   * Fetches and parses hpo-hra-relevant-dos.csv, keeping only rows whose `term` UBERON IRI
   * shows up in some loaded scenegraph node's `extras`, and stores them in `hpoHraRows`.
   */
  protected async loadHpoHraCsv(): Promise<void> {
    this.hpoHraRows.set([]);

    const [text, extrasUberonIris] = await Promise.all([
      firstValueFrom(this.http.get(HPO_HRA_CSV_URL, { responseType: 'text' })),
      this.collectExtrasUberonIris(),
    ]);

    const rows = parseCsv(text).filter((row) => extrasUberonIris.has(row.term));
    this.hpoHraRows.set(rows);
  }

  protected async logGlbMeshNames(): Promise<void> {
    const glbUrls = new Set(
      this.sceneNodes()
        .map((node) => node.scenegraph)
        .filter((url): url is string => typeof url === 'string'),
    );

    for (const url of glbUrls) {
      const { meshNames, uberonIds } = await getGlbMeshInfo(url);
      console.log(url, meshNames);
      console.log(url, uberonIds);
    }
  }

  /** Fetches every loaded scenegraph's `.glb` and unions the UBERON IRIs found in any node's `extras`. */
  private async collectExtrasUberonIris(): Promise<Set<string>> {
    const glbUrls = new Set(
      this.sceneNodes()
        .map((node) => node.scenegraph)
        .filter((url): url is string => typeof url === 'string'),
    );

    const iris = new Set<string>();
    for (const url of glbUrls) {
      const { uberonIris } = await getGlbMeshInfo(url);
      uberonIris.forEach((iri) => iris.add(iri));
    }
    return iris;
  }
}
