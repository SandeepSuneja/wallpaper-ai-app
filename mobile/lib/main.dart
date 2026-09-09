import 'package:flutter/material.dart';

import 'models/wallpaper.dart';
import 'services/api.dart';
import 'services/device_wallpaper.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  runApp(const WallcraftApp());
}

class WallcraftApp extends StatelessWidget {
  const WallcraftApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Wallcraft',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        brightness: Brightness.dark,
        colorScheme: ColorScheme.fromSeed(
          seedColor: const Color(0xFF3EB5B0),
          brightness: Brightness.dark,
        ),
        scaffoldBackgroundColor: const Color(0xFF071016),
        useMaterial3: true,
      ),
      home: const HomeScreen(),
    );
  }
}

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  final _api = WallpaperApi();
  final _wallpaperService = DeviceWallpaperService();
  final _promptController = TextEditingController(
    text:
        'Cinematic alley at blue hour, neon reflections on wet pavement, vertical mobile wallpaper, photoreal, no text',
  );

  List<WallpaperPreset> _presets = [];
  List<GalleryItem> _gallery = [];
  WallpaperPreset? _selectedPreset;
  GenerateResult? _result;
  bool _loadingPresets = true;
  bool _generating = false;
  bool _publishing = false;
  bool _publishOnGenerate = false;
  String? _error;
  String? _status;

  @override
  void initState() {
    super.initState();
    _bootstrap();
  }

  Future<void> _bootstrap() async {
    try {
      final presets = await _api.fetchPresets();
      final gallery = await _api.fetchGallery();
      setState(() {
        _presets = presets;
        _gallery = gallery;
        _selectedPreset = presets.isNotEmpty ? presets.first : null;
        _loadingPresets = false;
      });
    } catch (e) {
      setState(() {
        _loadingPresets = false;
        _error =
            'Could not reach API at ${_api.baseUrl}. Start the backend and use --dart-define=API_BASE=http://YOUR_PC_IP:8001 if needed.\n$e';
      });
    }
  }

  Future<void> _generate() async {
    final prompt = _promptController.text.trim();
    final preset = _selectedPreset;
    if (prompt.length < 3 || preset == null || _generating) {
      return;
    }

    setState(() {
      _generating = true;
      _error = null;
      _status = null;
    });

    try {
      final result = await _api.generate(
        prompt: prompt,
        preset: preset.id,
        publish: _publishOnGenerate,
      );
      final gallery = result.published ? await _api.fetchGallery() : _gallery;
      setState(() {
        _result = result;
        _gallery = gallery;
        _generating = false;
      });
    } catch (e) {
      setState(() {
        _generating = false;
        _error = e.toString();
      });
    }
  }

  Future<void> _publish() async {
    final result = _result;
    if (result == null || result.published || _publishing) {
      return;
    }
    setState(() => _publishing = true);
    try {
      await _api.publish(result);
      final gallery = await _api.fetchGallery();
      setState(() {
        _result = result.copyWith(published: true);
        _gallery = gallery;
        _publishing = false;
        _status = 'Published to gallery.';
      });
    } catch (e) {
      setState(() {
        _publishing = false;
        _error = e.toString();
      });
    }
  }

  Future<void> _saveOnly({String? imageUrl, String? id}) async {
    final url = imageUrl ?? _result?.imageUrl;
    final imageId = id ?? _result?.id;
    if (url == null || imageId == null) {
      return;
    }
    try {
      final file = await _api.downloadImage(url, imageId);
      final message = await _wallpaperService.saveToGallery(file);
      setState(() => _status = message);
    } catch (e) {
      setState(() => _error = e.toString());
    }
  }

  Future<void> _apply(WallpaperTarget target, {String? imageUrl, String? id}) async {
    final url = imageUrl ?? _result?.imageUrl;
    final imageId = id ?? _result?.id;
    if (url == null || imageId == null) {
      return;
    }

    try {
      final file = await _api.downloadImage(url, imageId);
      final message = await _wallpaperService.apply(file: file, target: target);
      setState(() => _status = message);
    } catch (e) {
      setState(() => _error = e.toString());
    }
  }

  void _openPreview({required String imageUrl, required String id, required int width, required int height}) {
    showDialog<void>(
      context: context,
      builder: (context) {
        final fullUrl = _api.absoluteImageUrl(imageUrl);
        return Dialog(
          backgroundColor: const Color(0xFF0B151C),
          insetPadding: const EdgeInsets.all(16),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Align(
                alignment: Alignment.centerRight,
                child: IconButton(
                  onPressed: () => Navigator.of(context).pop(),
                  icon: const Icon(Icons.close),
                ),
              ),
              Stack(
                children: [
                  InteractiveViewer(
                    child: Image.network(fullUrl, fit: BoxFit.contain),
                  ),
                  Positioned(
                    top: 8,
                    right: 8,
                    child: IconButton.filled(
                      onPressed: () => _saveOnly(imageUrl: imageUrl, id: id),
                      icon: const Icon(Icons.download),
                      tooltip: 'Download',
                    ),
                  ),
                ],
              ),
              Padding(
                padding: const EdgeInsets.all(12),
                child: Wrap(
                  spacing: 8,
                  runSpacing: 8,
                  children: [
                    FilledButton.tonal(
                      onPressed: () => _apply(WallpaperTarget.home, imageUrl: imageUrl, id: id),
                      child: const Text('Home screen'),
                    ),
                    FilledButton.tonal(
                      onPressed: () => _apply(WallpaperTarget.lock, imageUrl: imageUrl, id: id),
                      child: const Text('Lock screen'),
                    ),
                    Text('$width×$height', style: const TextStyle(color: Color(0xFFA9B7C3))),
                  ],
                ),
              ),
            ],
          ),
        );
      },
    );
  }

  @override
  void dispose() {
    _promptController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.fromLTRB(20, 16, 20, 32),
          children: [
            const Text(
              'Wallcraft',
              style: TextStyle(fontSize: 34, fontWeight: FontWeight.w600, letterSpacing: -0.5),
            ),
            const SizedBox(height: 6),
            const Text(
              'Portrait wallpapers for your phone. Quality is tuned automatically for the resolution you pick.',
              style: TextStyle(color: Color(0xFFA9B7C3), height: 1.4),
            ),
            const SizedBox(height: 20),
            TextField(
              controller: _promptController,
              maxLines: 5,
              maxLength: 2000,
              decoration: const InputDecoration(
                labelText: 'Prompt',
                border: OutlineInputBorder(),
              ),
            ),
            const SizedBox(height: 12),
            if (_loadingPresets)
              const LinearProgressIndicator()
            else
              DropdownButtonFormField<WallpaperPreset>(
                // ignore: deprecated_member_use
                value: _selectedPreset,
                decoration: const InputDecoration(
                  labelText: 'Resolution',
                  border: OutlineInputBorder(),
                ),
                items: _presets
                    .map(
                      (preset) => DropdownMenuItem(
                        value: preset,
                        child: Text(preset.label),
                      ),
                    )
                    .toList(),
                onChanged: (value) => setState(() => _selectedPreset = value),
              ),
            const SizedBox(height: 8),
            CheckboxListTile(
              contentPadding: EdgeInsets.zero,
              value: _publishOnGenerate,
              onChanged: (value) => setState(() => _publishOnGenerate = value ?? false),
              title: const Text('Publish after generate'),
              controlAffinity: ListTileControlAffinity.leading,
            ),
            const SizedBox(height: 8),
            FilledButton(
              onPressed: _generating ? null : _generate,
              child: Text(_generating ? 'Rendering…' : 'Generate wallpaper'),
            ),
            if (_error != null) ...[
              const SizedBox(height: 12),
              Text(_error!, style: const TextStyle(color: Color(0xFFFFB4A8))),
            ],
            if (_status != null) ...[
              const SizedBox(height: 12),
              Text(_status!, style: const TextStyle(color: Color(0xFF9ED9CF))),
            ],
            const SizedBox(height: 24),
            const Text('Wallpaper', style: TextStyle(fontSize: 22, fontWeight: FontWeight.w600)),
            const SizedBox(height: 8),
            if (_generating)
              const AspectRatio(
                aspectRatio: 9 / 16,
                child: Center(child: CircularProgressIndicator()),
              )
            else if (_result != null) ...[
              GestureDetector(
                onTap: () => _openPreview(
                  imageUrl: _result!.imageUrl,
                  id: _result!.id,
                  width: _result!.width,
                  height: _result!.height,
                ),
                child: ClipRRect(
                  borderRadius: BorderRadius.circular(12),
                  child: AspectRatio(
                    aspectRatio: 9 / 16,
                    child: Image.network(
                      _api.absoluteImageUrl(_result!.imageUrl),
                      fit: BoxFit.cover,
                    ),
                  ),
                ),
              ),
              const SizedBox(height: 12),
              Wrap(
                spacing: 8,
                runSpacing: 8,
                children: [
                  OutlinedButton(
                    onPressed: () => _openPreview(
                      imageUrl: _result!.imageUrl,
                      id: _result!.id,
                      width: _result!.width,
                      height: _result!.height,
                    ),
                    child: const Text('Preview'),
                  ),
                  OutlinedButton(
                    onPressed: () => _apply(WallpaperTarget.home),
                    child: const Text('Home screen'),
                  ),
                  OutlinedButton(
                    onPressed: () => _apply(WallpaperTarget.lock),
                    child: const Text('Lock screen'),
                  ),
                  if (!_result!.published)
                    OutlinedButton(
                      onPressed: _publishing ? null : _publish,
                      child: Text(_publishing ? 'Publishing…' : 'Publish'),
                    ),
                ],
              ),
            ] else
              Container(
                height: 220,
                alignment: Alignment.center,
                decoration: BoxDecoration(
                  color: const Color(0xFF0B151C),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: const Text(
                  'Your portrait wallpaper will appear here.',
                  style: TextStyle(color: Color(0xFF93A6B4)),
                ),
              ),
            const SizedBox(height: 28),
            const Text('Published gallery', style: TextStyle(fontSize: 22, fontWeight: FontWeight.w600)),
            const SizedBox(height: 8),
            if (_gallery.isEmpty)
              const Text(
                'No published portrait wallpapers yet.',
                style: TextStyle(color: Color(0xFF93A6B4)),
              )
            else
              GridView.builder(
                shrinkWrap: true,
                physics: const NeverScrollableScrollPhysics(),
                itemCount: _gallery.length,
                gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                  crossAxisCount: 2,
                  crossAxisSpacing: 10,
                  mainAxisSpacing: 10,
                  childAspectRatio: 0.68,
                ),
                itemBuilder: (context, index) {
                  final item = _gallery[index];
                  final url = _api.absoluteImageUrl(item.imageUrl);
                  return GestureDetector(
                    onTap: () => _openPreview(
                      imageUrl: item.imageUrl,
                      id: item.id,
                      width: item.width,
                      height: item.height,
                    ),
                    child: ClipRRect(
                      borderRadius: BorderRadius.circular(10),
                      child: Stack(
                        fit: StackFit.expand,
                        children: [
                          Image.network(url, fit: BoxFit.cover),
                          Positioned(
                            top: 8,
                            right: 8,
                            child: Material(
                              color: Colors.black54,
                              shape: const CircleBorder(),
                              child: IconButton(
                                icon: const Icon(Icons.download, size: 18),
                                onPressed: () => _saveOnly(
                                  imageUrl: item.imageUrl,
                                  id: item.id,
                                ),
                              ),
                            ),
                          ),
                          Positioned(
                            left: 8,
                            right: 8,
                            bottom: 8,
                            child: Text(
                              '${item.width}×${item.height}',
                              style: const TextStyle(fontSize: 12, color: Colors.white),
                            ),
                          ),
                        ],
                      ),
                    ),
                  );
                },
              ),
          ],
        ),
      ),
    );
  }
}
