import 'package:flutter/material.dart';

class AudioPlayerWidget extends StatelessWidget {
  const AudioPlayerWidget({super.key, required this.enabled, required this.onPlay});

  final bool enabled;
  final VoidCallback onPlay;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return FilledButton.tonalIcon(
      onPressed: enabled ? onPlay : null,
      icon: const Icon(Icons.volume_up_rounded),
      label: const Text('Listen'),
      style: FilledButton.styleFrom(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
        foregroundColor: scheme.onSecondaryContainer,
      ),
    );
  }
}
