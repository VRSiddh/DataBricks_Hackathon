import 'dart:convert';
import 'dart:typed_data';

import 'package:audioplayers/audioplayers.dart';

/// Plays base64-encoded audio returned by the API (WAV/MP3 depending on provider).
class AudioService {
  final AudioPlayer _player = AudioPlayer();

  Future<void> playBase64(String? base64) async {
    if (base64 == null || base64.isEmpty) return;
    final bytes = base64Decode(base64);
    await _player.stop();
    await _player.play(BytesSource(Uint8List.fromList(bytes)));
  }

  Future<void> stop() => _player.stop();
}
