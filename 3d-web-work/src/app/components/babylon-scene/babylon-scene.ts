import {
  AfterViewInit,
  Component,
  ElementRef,
  HostListener,
  OnDestroy,
  ViewChild,
} from '@angular/core';
import {
  AbstractMesh,
  ArcRotateCamera,
  Color3,
  Engine,
  HemisphericLight,
  ImportMeshAsync,
  MeshBuilder,
  PBRMaterial,
  Scene,
  Vector3,
} from '@babylonjs/core';
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
  private readonly boxSize = 0.1;
  private kidneyMeshes: AbstractMesh[] = [];

  ngAfterViewInit(): void {
    try {
      this.engine = new Engine(this.canvasRef.nativeElement, true);
    } catch {
      return;
    }

    this.scene = this.createScene(this.engine);
    this.loadKidney(this.scene, this.boxSize);
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

    const camera = new ArcRotateCamera(
      'camera',
      -Math.PI / 2,
      Math.PI / 2.5,
      100,
      new Vector3(this.boxSize, 0, 0),
      scene,
    );
    camera.attachControl(this.canvasRef.nativeElement, true);
    camera.lowerRadiusLimit = this.boxSize;
    camera.upperRadiusLimit = this.boxSize * 50;

    const light = new HemisphericLight('light', new Vector3(0, 1, 0), scene);

    const box = MeshBuilder.CreateBox('box', { size: this.boxSize }, scene);

    return scene;
  }

  private async loadKidney(scene: Scene, referenceSize: number): Promise<void> {
    try {
      const result = await ImportMeshAsync(KIDNEY_GLB_URL, scene);
      const root = result.meshes[0];

      // // Normalize scale so the kidney is roughly the same size as the box
      // const rawBounds = root.getHierarchyBoundingVectors();
      // const rawSize = rawBounds.max.subtract(rawBounds.min);
      // const scale = referenceSize / Math.max(rawSize.x, rawSize.y, rawSize.z);
      // root.scaling.scaleInPlace(scale);

      // Recenter the model, then place it beside the box
      const bounds = root.getHierarchyBoundingVectors();
      const center = bounds.max.add(bounds.min).scale(0.5);
      root.position.subtractInPlace(center);
      root.position.x += referenceSize * 2;
      root.scaling = new Vector3(5, 5, 5);

      this.kidneyMeshes = result.meshes.filter((mesh) => mesh.material);

      // Point the camera at the kidney now that we know its final position/size
      const kidneyBounds = root.getHierarchyBoundingVectors();
      const kidneyCenter = kidneyBounds.max.add(kidneyBounds.min).scale(0.5);
      const kidneySize = kidneyBounds.max.subtract(kidneyBounds.min).length();

      const camera = scene.activeCamera as ArcRotateCamera;
      camera.target = kidneyCenter;
      camera.radius = kidneySize * 2;
      camera.lowerRadiusLimit = kidneySize * 0.1;
      camera.upperRadiusLimit = kidneySize * 5;
    } catch (err) {
      console.error('Failed to load kidney model', err);
    }
  }

  public helloworld(): void {
    console.log('HELLO');
  }

  public onToggle(event: Event): void {
    const checked = (event.target as HTMLInputElement).checked;
    console.log('toggle changed', checked);
  }

  public changeKidneyColor(): void {
    const color = Color3.FromHexString('#FF0043');
    for (const mesh of this.kidneyMeshes) {
      console.log(mesh);
      (mesh.material as PBRMaterial).albedoColor = color;
    }
  }

}
