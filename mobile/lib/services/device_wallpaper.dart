import 'dart:io';

import 'package:async_wallpaper/async_wallpaper.dart';
import 'package:flutter/foundation.dart';
import 'package:gal/gal.dart';
import 'package:permission_handler/permission_handler.dart';

enum WallpaperTarget { home, lock, both }

class DeviceWallpaperService {
  Future<String> saveToGallery(File file) async {
    final granted = await Gal.requestAccess();
    if (!granted) {
      throw Exception('Photo library access is required to save the wallpaper.');
    }
    await Gal.putImage(file.path);
    return 'Saved to your photo library.';
  }

  Future<String> apply({
    required File file,
    required WallpaperTarget target,
  }) async {
    if (Platform.isAndroid) {
      final status = await Permission.storage.request();
      // Android 10+ often doesn't need storage for wallpaper; ignore permanent denial softly.
      debugPrint('storage permission: $status');

      final location = switch (target) {
        WallpaperTarget.home => AsyncWallpaper.HOME_SCREEN,
        WallpaperTarget.lock => AsyncWallpaper.LOCK_SCREEN,
        WallpaperTarget.both => AsyncWallpaper.BOTH_SCREENS,
      };

      final ok = await AsyncWallpaper.setWallpaperFromFile(
        filePath: file.path,
        wallpaperLocation: location,
        goToHome: false,
      );
      if (ok != true) {
        throw Exception('Could not set wallpaper on this device.');
      }
      return switch (target) {
        WallpaperTarget.home => 'Set as home screen wallpaper.',
        WallpaperTarget.lock => 'Set as lock screen wallpaper.',
        WallpaperTarget.both => 'Set as home and lock screen wallpaper.',
      };
    }

    // iOS does not allow apps to set wallpaper/lock screen directly.
    final granted = await Gal.requestAccess();
    if (!granted) {
      throw Exception('Photo library access is required to save the wallpaper.');
    }
    await Gal.putImage(file.path);
    return 'Saved to Photos. Open the image → Share → Use as Wallpaper to set home or lock screen.';
  }
}
