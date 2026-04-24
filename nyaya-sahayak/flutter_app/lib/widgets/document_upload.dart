import 'package:flutter/material.dart';

class DocumentUploadCard extends StatelessWidget {
  const DocumentUploadCard({
    super.key,
    required this.onPick,
    this.busy = false,
  });

  final VoidCallback onPick;
  final bool busy;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return Material(
      color: scheme.surfaceContainerHighest.withValues(alpha: 0.35),
      borderRadius: BorderRadius.circular(24),
      child: InkWell(
        borderRadius: BorderRadius.circular(24),
        onTap: busy ? null : onPick,
        child: Padding(
          padding: const EdgeInsets.all(22),
          child: Row(
            children: [
              Icon(Icons.upload_file_rounded, size: 40, color: scheme.primary),
              const SizedBox(width: 16),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      busy ? 'Processing…' : 'Upload FIR / notice / PDF',
                      style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w700),
                    ),
                    const SizedBox(height: 6),
                    Text(
                      'PDF (≤10 pages recommended) or clear photo • max 5MB images / 8MB PDF',
                      style: Theme.of(context).textTheme.bodySmall?.copyWith(color: scheme.onSurfaceVariant),
                    ),
                  ],
                ),
              ),
              const Icon(Icons.chevron_right_rounded),
            ],
          ),
        ),
      ),
    );
  }
}
