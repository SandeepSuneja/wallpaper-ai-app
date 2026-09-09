import { Component, OnInit, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { HttpErrorResponse } from '@angular/common/http';

import {
  ApplyTarget,
  DesktopPreset,
  GalleryItem,
  GenerateResponse,
  HealthResponse,
  Orientation,
} from './models/wallpaper';
import { WallpaperService } from './services/wallpaper.service';

interface PreviewItem {
  id: string;
  prompt: string;
  width: number;
  height: number;
  orientation: Orientation;
  seed: number;
  image_url: string;
}

@Component({
  selector: 'app-root',
  imports: [FormsModule],
  templateUrl: './app.html',
  styleUrl: './app.scss',
})
export class App implements OnInit {
  private readonly wallpaperService = inject(WallpaperService);

  readonly presets = signal<DesktopPreset[]>([]);
  readonly gallery = signal<GalleryItem[]>([]);
  readonly health = signal<HealthResponse | null>(null);
  readonly result = signal<GenerateResponse | null>(null);
  readonly previewItem = signal<PreviewItem | null>(null);
  readonly generating = signal(false);
  readonly publishing = signal(false);
  readonly applyHint = signal<string | null>(null);
  readonly error = signal<string | null>(null);

  prompt =
    'Cinematic alpine lake at dawn, soft mist over glassy water, pine ridges in deep teal shadow, warm amber light on distant peaks, photoreal, no text';
  selectedPreset = 'fhd_16_9';
  publishOnGenerate = false;

  ngOnInit(): void {
    this.loadPresets();
    this.loadGallery();

    this.wallpaperService.getHealth().subscribe({
      next: (res) => this.health.set(res),
      error: () => this.health.set(null),
    });
  }

  generate(): void {
    const prompt = this.prompt.trim();
    if (prompt.length < 3 || this.generating()) {
      return;
    }

    this.generating.set(true);
    this.error.set(null);
    this.applyHint.set(null);

    this.wallpaperService
      .generate({
        prompt,
        orientation: 'landscape',
        preset: this.selectedPreset,
        publish: this.publishOnGenerate,
      })
      .subscribe({
        next: (res) => {
          this.result.set(res);
          this.previewItem.set(null);
          this.generating.set(false);
          if (res.published) {
            this.loadGallery();
          }
        },
        error: (err: HttpErrorResponse) => {
          const detail = err.error?.detail;
          this.error.set(typeof detail === 'string' ? detail : 'Generation failed. Check the backend logs.');
          this.generating.set(false);
        },
      });
  }

  publishCurrent(): void {
    const current = this.result();
    if (!current || current.published || this.publishing()) {
      return;
    }

    this.publishing.set(true);
    this.wallpaperService.publish(current).subscribe({
      next: () => {
        this.result.set({ ...current, published: true });
        this.publishing.set(false);
        this.loadGallery();
      },
      error: (err: HttpErrorResponse) => {
        const detail = err.error?.detail;
        this.error.set(typeof detail === 'string' ? detail : 'Publish failed.');
        this.publishing.set(false);
      },
    });
  }

  openPreview(): void {
    const current = this.result();
    if (!current) {
      return;
    }
    this.previewItem.set({
      id: current.id,
      prompt: current.prompt,
      width: current.width,
      height: current.height,
      orientation: current.orientation,
      seed: current.seed,
      image_url: current.image_url,
    });
  }

  openGalleryPreview(item: GalleryItem): void {
    this.previewItem.set({
      id: item.id,
      prompt: item.prompt,
      width: item.width,
      height: item.height,
      orientation: item.orientation,
      seed: item.seed,
      image_url: item.image_url,
    });
  }

  closePreview(): void {
    this.previewItem.set(null);
  }

  downloadPreview(): void {
    const item = this.previewItem();
    if (!item) {
      return;
    }
    this.download(item.image_url, item.id, item.width, item.height);
  }

  download(url?: string, id?: string, width?: number, height?: number): void {
    const current = this.result();
    const href = url ?? current?.image_url;
    if (!href) {
      return;
    }
    const link = document.createElement('a');
    link.href = href;
    link.download = `wallcraft-${width ?? current?.width}x${height ?? current?.height}-${id ?? current?.id}.png`;
    link.click();
  }

  onThumbnailDownload(event: Event, item: GalleryItem): void {
    event.stopPropagation();
    this.download(item.image_url, item.id, item.width, item.height);
  }

  applyAs(target: ApplyTarget, source: 'result' | 'preview' = 'result'): void {
    const item =
      source === 'preview'
        ? this.previewItem()
        : this.result()
          ? {
              id: this.result()!.id,
              image_url: this.result()!.image_url,
              width: this.result()!.width,
              height: this.result()!.height,
            }
          : null;

    if (!item) {
      return;
    }

    this.download(item.image_url, item.id, item.width, item.height);

    const isMac = /Mac|iPhone|iPad/.test(navigator.platform) || navigator.userAgent.includes('Mac');
    if (target === 'background') {
      this.applyHint.set(
        isMac
          ? 'Image downloaded. On macOS: System Settings → Wallpaper → Add Folder / drag in the PNG.'
          : 'Image downloaded. On Windows: right-click the PNG → Set as desktop background.',
      );
    } else {
      this.applyHint.set(
        isMac
          ? 'Image downloaded. On macOS: System Settings → Wallpaper → set as Screen Saver / Lock Screen from options, or add the image in Wallpaper.'
          : 'Image downloaded. On Windows: Settings → Personalization → Lock screen → Browse photos and choose the PNG.',
      );
    }
  }

  activePresetLabel(): string {
    return this.presets().find((p) => p.id === this.selectedPreset)?.label ?? this.selectedPreset;
  }

  private loadPresets(): void {
    this.wallpaperService.getPresets('landscape').subscribe({
      next: (res) => {
        this.presets.set(res.presets);
        if (!res.presets.some((p) => p.id === this.selectedPreset) && res.presets[0]) {
          this.selectedPreset = res.presets[0].id;
        }
      },
      error: () => this.error.set('Could not load presets. Is the API running on port 8001?'),
    });
  }

  private loadGallery(): void {
    this.wallpaperService.getGallery('landscape').subscribe({
      next: (res) => this.gallery.set(res.items),
      error: () => this.gallery.set([]),
    });
  }
}
