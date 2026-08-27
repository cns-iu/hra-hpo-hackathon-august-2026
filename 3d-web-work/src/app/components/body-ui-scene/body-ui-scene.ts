import { HttpClient } from '@angular/common/http';
import { Component, CUSTOM_ELEMENTS_SCHEMA, inject, signal } from '@angular/core';

const REFERENCE_ORGAN_SCENE_URL =
  'https://apps.humanatlas.io/api/v1/reference-organ-scene?organ-iri=http%3A%2F%2Fpurl.obolibrary.org%2Fobo%2FUBERON_0000059&sex=male';

/** Minimal shape of the nodes the hra-body-ui `scene` array holds; only the field we read/write is typed. */
interface SceneNode {
  color?: [number, number, number, number];
  scenegraph?: string;
  opacity?: number;
  [key: string]: unknown;
  entityId?: string;
}

/** Reads the mesh names out of a glTF binary (.glb) file's JSON chunk. */
async function getGlbMeshNames(url: string): Promise<string[]> {
  const buf = await fetch(url).then((r) => r.arrayBuffer());
  const dv = new DataView(buf);
  const jsonLength = dv.getUint32(12, true);
  const json = JSON.parse(new TextDecoder().decode(new Uint8Array(buf, 20, jsonLength)));
  return json.meshes.map((mesh: { name: string }) => mesh.name);
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

  constructor() {
    this.http.get<SceneNode[]>(REFERENCE_ORGAN_SCENE_URL).subscribe((nodes) => {
      this.originalSceneNodes = nodes;

      this.originalSceneNodes.forEach((node) => {
        console.log(`Node: ${node.scenegraph}`);
      });

      this.sceneNodes.set(nodes.filter((node) => node.scenegraph !== undefined));
    });
  }

  protected colorAllRed(): void {
    this.sceneNodes.update((nodes) =>
      nodes.map((node) => ({
        ...node,
        color: [255, 0, 0, node.color ? node.color[3] : 255] as [number, number, number, number],
      })),
    );
  }

  protected resetColors(): void {
    this.sceneNodes.set(this.originalSceneNodes);
  }

  protected setGlbOpacity(event: Event): void {
    const opacity = Number((event.target as HTMLInputElement).value);

    // Only scenegraph (glTF) nodes read `opacity` at all - it's applied as that
    // node's whole-layer alpha, covering every mesh inside its .glb.
    this.sceneNodes.update((nodes) =>
      nodes.map((node) => (node.scenegraph ? { ...node, opacity } : node)),
    );
  }

  protected async logGlbMeshNames(): Promise<void> {
    const glbUrls = new Set(
      this.sceneNodes()
        .map((node) => node.scenegraph)
        .filter((url): url is string => typeof url === 'string'),
    );

    for (const url of glbUrls) {
      const meshNames = await getGlbMeshNames(url);
      console.log(url, meshNames);
    }
  }
}
