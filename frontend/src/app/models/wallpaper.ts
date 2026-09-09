export type Orientation = 'landscape' | 'portrait';

export interface DesktopPreset {
  id: string;
  label: string;
  width: number;
  height: number;
  aspect: string;
  orientation: Orientation;
  steps: number;
  guidance_scale: number;
}

export interface GenerateRequest {
  prompt: string;
  orientation: Orientation;
  preset: string;
  publish: boolean;
}

export interface GenerateResponse {
  id: string;
  prompt: string;
  width: number;
  height: number;
  orientation: Orientation;
  seed: number;
  steps: number;
  guidance_scale: number;
  model_id: string;
  image_url: string;
  mock: boolean;
  published: boolean;
  render_width?: number | null;
  render_height?: number | null;
}

export interface GalleryItem {
  id: string;
  prompt: string;
  width: number;
  height: number;
  orientation: Orientation;
  seed: number;
  steps: number;
  guidance_scale: number;
  model_id: string;
  image_url: string;
  published_at: string;
}

export interface HealthResponse {
  status: string;
  model_id: string;
  device: string;
  model_loaded: boolean;
  mock_generation: boolean;
  cuda_available: boolean;
  gpu_name?: string | null;
  vram_total_gb?: number | null;
}

export type ApplyTarget = 'background' | 'lockscreen';
