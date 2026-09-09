import 'dart:convert';
import 'dart:io';

import 'package:http/http.dart' as http;
import 'package:path/path.dart' as p;
import 'package:path_provider/path_provider.dart';

import '../models/wallpaper.dart';

class WallpaperApi {
  WallpaperApi({String? baseUrl})
      : baseUrl = baseUrl ??
            const String.fromEnvironment(
              'API_BASE',
              defaultValue: 'http://10.0.2.2:8001',
            );

  final String baseUrl;

  Uri _uri(String path, [Map<String, String>? query]) {
    return Uri.parse('$baseUrl$path').replace(queryParameters: query);
  }

  String absoluteImageUrl(String pathOrUrl) {
    if (pathOrUrl.startsWith('http')) {
      return pathOrUrl;
    }
    return '$baseUrl$pathOrUrl';
  }

  Future<List<WallpaperPreset>> fetchPresets() async {
    final response = await http.get(_uri('/api/presets', {'orientation': 'portrait'}));
    if (response.statusCode != 200) {
      throw Exception('Failed to load presets (${response.statusCode})');
    }
    final body = jsonDecode(response.body) as Map<String, dynamic>;
    final presets = body['presets'] as List<dynamic>;
    return presets.map((e) => WallpaperPreset.fromJson(e as Map<String, dynamic>)).toList();
  }

  Future<List<GalleryItem>> fetchGallery() async {
    final response = await http.get(_uri('/api/gallery', {'orientation': 'portrait'}));
    if (response.statusCode != 200) {
      throw Exception('Failed to load gallery (${response.statusCode})');
    }
    final body = jsonDecode(response.body) as Map<String, dynamic>;
    final items = body['items'] as List<dynamic>;
    return items.map((e) => GalleryItem.fromJson(e as Map<String, dynamic>)).toList();
  }

  Future<GenerateResult> generate({
    required String prompt,
    required String preset,
    bool publish = false,
  }) async {
    final response = await http
        .post(
          _uri('/api/generate'),
          headers: {'Content-Type': 'application/json'},
          body: jsonEncode({
            'prompt': prompt,
            'orientation': 'portrait',
            'preset': preset,
            'publish': publish,
          }),
        )
        .timeout(const Duration(minutes: 10));

    if (response.statusCode != 200) {
      final detail = _extractDetail(response.body);
      throw Exception(detail ?? 'Generation failed (${response.statusCode})');
    }
    return GenerateResult.fromJson(jsonDecode(response.body) as Map<String, dynamic>);
  }

  Future<void> publish(GenerateResult result) async {
    final response = await http.post(
      _uri('/api/images/${result.id}/publish'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({
        'prompt': result.prompt,
        'width': result.width,
        'height': result.height,
        'orientation': result.orientation,
        'seed': result.seed,
        'steps': result.steps,
        'guidance_scale': result.guidanceScale,
      }),
    );
    if (response.statusCode != 200) {
      throw Exception('Publish failed (${response.statusCode})');
    }
  }

  Future<File> downloadImage(String imageUrl, String id) async {
    final url = absoluteImageUrl(imageUrl);
    final response = await http.get(Uri.parse(url));
    if (response.statusCode != 200) {
      throw Exception('Download failed (${response.statusCode})');
    }
    final dir = await getTemporaryDirectory();
    final file = File(p.join(dir.path, 'wallcraft-$id.png'));
    await file.writeAsBytes(response.bodyBytes);
    return file;
  }

  String? _extractDetail(String body) {
    try {
      final json = jsonDecode(body);
      if (json is Map && json['detail'] is String) {
        return json['detail'] as String;
      }
    } catch (_) {}
    return null;
  }
}
