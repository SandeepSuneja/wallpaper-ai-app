class WallpaperPreset {
  WallpaperPreset({
    required this.id,
    required this.label,
    required this.width,
    required this.height,
    required this.aspect,
    required this.orientation,
    required this.steps,
    required this.guidanceScale,
  });

  final String id;
  final String label;
  final int width;
  final int height;
  final String aspect;
  final String orientation;
  final int steps;
  final double guidanceScale;

  factory WallpaperPreset.fromJson(Map<String, dynamic> json) {
    return WallpaperPreset(
      id: json['id'] as String,
      label: json['label'] as String,
      width: json['width'] as int,
      height: json['height'] as int,
      aspect: json['aspect'] as String,
      orientation: json['orientation'] as String,
      steps: json['steps'] as int,
      guidanceScale: (json['guidance_scale'] as num).toDouble(),
    );
  }
}

class GenerateResult {
  GenerateResult({
    required this.id,
    required this.prompt,
    required this.width,
    required this.height,
    required this.orientation,
    required this.seed,
    required this.steps,
    required this.guidanceScale,
    required this.modelId,
    required this.imageUrl,
    required this.mock,
    required this.published,
  });

  final String id;
  final String prompt;
  final int width;
  final int height;
  final String orientation;
  final int seed;
  final int steps;
  final double guidanceScale;
  final String modelId;
  final String imageUrl;
  final bool mock;
  final bool published;

  factory GenerateResult.fromJson(Map<String, dynamic> json) {
    return GenerateResult(
      id: json['id'] as String,
      prompt: json['prompt'] as String,
      width: json['width'] as int,
      height: json['height'] as int,
      orientation: json['orientation'] as String,
      seed: json['seed'] as int,
      steps: json['steps'] as int,
      guidanceScale: (json['guidance_scale'] as num).toDouble(),
      modelId: json['model_id'] as String,
      imageUrl: json['image_url'] as String,
      mock: json['mock'] as bool? ?? false,
      published: json['published'] as bool? ?? false,
    );
  }

  GenerateResult copyWith({bool? published}) {
    return GenerateResult(
      id: id,
      prompt: prompt,
      width: width,
      height: height,
      orientation: orientation,
      seed: seed,
      steps: steps,
      guidanceScale: guidanceScale,
      modelId: modelId,
      imageUrl: imageUrl,
      mock: mock,
      published: published ?? this.published,
    );
  }
}

class GalleryItem {
  GalleryItem({
    required this.id,
    required this.prompt,
    required this.width,
    required this.height,
    required this.orientation,
    required this.seed,
    required this.imageUrl,
    required this.publishedAt,
  });

  final String id;
  final String prompt;
  final int width;
  final int height;
  final String orientation;
  final int seed;
  final String imageUrl;
  final String publishedAt;

  factory GalleryItem.fromJson(Map<String, dynamic> json) {
    return GalleryItem(
      id: json['id'] as String,
      prompt: json['prompt'] as String,
      width: json['width'] as int,
      height: json['height'] as int,
      orientation: json['orientation'] as String,
      seed: json['seed'] as int,
      imageUrl: json['image_url'] as String,
      publishedAt: json['published_at'] as String,
    );
  }
}
