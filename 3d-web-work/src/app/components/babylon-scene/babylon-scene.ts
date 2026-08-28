import { AfterViewInit, Component, ElementRef, HostListener, OnDestroy, ViewChild } from '@angular/core';
import { ArcRotateCamera, Engine, HemisphericLight, ImportMeshAsync, Scene, Vector3 } from '@babylonjs/core';
import '@babylonjs/loaders/glTF';

const KIDNEY_GLB_URL =
  'https://cdn.humanatlas.io/digital-objects/ref-organ/kidney-male-right/v1.3/assets/3d-vh-m-kidney-r.glb';

@Component({
  selector: 'app-babylon-scene',
  imports: [],
  templateUrl: './babylon-scene.html',
  styleUrl: './babylon-scene.css',
})
export class BabylonScene implements AfterViewInit, OnDestroy {
  @ViewChild('renderCanvas', { static: true })
  private canvasRef!: ElementRef<HTMLCanvasElement>;

  private engine?: Engine;
  private scene?: Scene;

  ngAfterViewInit(): void {
    this.engine = new Engine(this.canvasRef.nativeElement, true);
    this.scene = this.createScene(this.engine);
    this.loadKidney(this.scene);
    this.engine.runRenderLoop(() => this.scene?.render());
  }

  @HostListener('window:resize')
  onResize(): void {
    this.engine?.resize();
  }

  ngOnDestroy(): void {
    this.scene?.dispose();
    this.engine?.dispose();
  }

  private createScene(engine: Engine): Scene {
    const scene = new Scene(engine);

    const camera = new ArcRotateCamera('camera', -Math.PI / 2, Math.PI / 2.5, 1, Vector3.Zero(), scene);
    camera.attachControl(this.canvasRef.nativeElement, true);

    new HemisphericLight('light', new Vector3(0, 1, 0), scene);

    return scene;
  }

  private async loadKidney(scene: Scene): Promise<void> {
    try {
      const result = await ImportMeshAsync(KIDNEY_GLB_URL, scene);
      const root = result.meshes[0];

      const bounds = root.getHierarchyBoundingVectors();
      const center = bounds.max.add(bounds.min).scale(0.5);
      root.position.subtractInPlace(center);

      const size = bounds.max.subtract(bounds.min).length();
      const camera = scene.activeCamera as ArcRotateCamera;
      camera.radius = size * 2;
      camera.lowerRadiusLimit = size * 0.1;
      camera.upperRadiusLimit = size * 5;
    } catch (err) {
      console.error('Failed to load kidney model', err);
    }
  }

  /** Enters an immersive-vr WebXR session (Quest Browser and other WebXR-capable browsers). */
  protected async enterVr(): Promise<void> {
    if (!this.scene) return;

    const xr = await this.scene.createDefaultXRExperienceAsync({
      uiOptions: { sessionMode: 'immersive-vr' },
    });

    if (!xr.baseExperience) {
      console.error('WebXR immersive-vr is not supported on this device/browser.');
    }
  }
}
