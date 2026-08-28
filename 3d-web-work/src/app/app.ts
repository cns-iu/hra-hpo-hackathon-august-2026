import { Component, OnInit, inject, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { BabylonScene } from './components/babylon-scene/babylon-scene';
import { BodyUiScene } from './components/body-ui-scene/body-ui-scene';
import { firstValueFrom } from 'rxjs';

const SAMPLE_CSV_URL = 'https://purl.humanatlas.io/ref-organ/kidney-male-right';

@Component({
  selector: 'app-root',
  imports: [BabylonScene, BodyUiScene],
  templateUrl: './app.html',
  styleUrl: './app.css',
})
export class App implements OnInit {
  private readonly http = inject(HttpClient);
  private kidneyPurlJson?: object;

  protected readonly showBabylon = signal(false);

  protected toggleView(): void {
    this.showBabylon.update((value) => !value);
  }

  ngOnInit(): void {
    this.process_purl_data(SAMPLE_CSV_URL).then((json) => {
      this.kidneyPurlJson = json;
      console.log(this.kidneyPurlJson);
    });
  }

  async process_purl_data(url: string): Promise<object> {
    const json = await firstValueFrom(
      this.http.get(url, { headers: { Accept: 'application/json' } }),
    );
    return json;
  }
}
