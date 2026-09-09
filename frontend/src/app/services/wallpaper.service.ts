import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import {
  DesktopPreset,
  GalleryItem,
  GenerateRequest,
  GenerateResponse,
  HealthResponse,
  Orientation,
} from '../models/wallpaper';

@Injectable({ providedIn: 'root' })
export class WallpaperService {
  private readonly http = inject(HttpClient);
  private readonly apiBase = '/api';

  getHealth(): Observable<HealthResponse> {
    return this.http.get<HealthResponse>(`${this.apiBase}/health`);
  }

  getPresets(orientation: Orientation = 'landscape'): Observable<{ presets: DesktopPreset[] }> {
    const params = new HttpParams().set('orientation', orientation);
    return this.http.get<{ presets: DesktopPreset[] }>(`${this.apiBase}/presets`, { params });
  }

  getGallery(orientation?: Orientation): Observable<{ items: GalleryItem[] }> {
    let params = new HttpParams();
    if (orientation) {
      params = params.set('orientation', orientation);
    }
    return this.http.get<{ items: GalleryItem[] }>(`${this.apiBase}/gallery`, { params });
  }

  generate(payload: GenerateRequest): Observable<GenerateResponse> {
    return this.http.post<GenerateResponse>(`${this.apiBase}/generate`, payload);
  }

  publish(result: GenerateResponse): Observable<{ id: string; published: boolean; image_url: string }> {
    return this.http.post<{ id: string; published: boolean; image_url: string }>(
      `${this.apiBase}/images/${result.id}/publish`,
      {
        prompt: result.prompt,
        width: result.width,
        height: result.height,
        orientation: result.orientation,
        seed: result.seed,
        steps: result.steps,
        guidance_scale: result.guidance_scale,
      },
    );
  }
}
