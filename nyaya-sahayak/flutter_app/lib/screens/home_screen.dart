import 'package:flutter/material.dart';

import '../config/routes.dart';

class HomeScreen extends StatelessWidget {
  const HomeScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return Scaffold(
      body: CustomScrollView(
        slivers: [
          const SliverAppBar(
            pinned: true,
            title: Text('Nyaya-Sahayak'),
          ),
          SliverPadding(
            padding: const EdgeInsets.fromLTRB(18, 8, 18, 24),
            sliver: SliverList.list(
              children: [
                Text(
                  'न्याय सहायक • BNS-aware legal assistant',
                  style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w800),
                ),
                const SizedBox(height: 10),
                Text(
                  'One calm interface for everyone — from a first-time complainant to a busy practitioner. '
                  'Upload a document, pick your language, and get grounded guidance with Bharatiya Nyaya Sanhita (BNS) context.',
                  style: Theme.of(context).textTheme.bodyLarge?.copyWith(height: 1.35),
                ),
                const SizedBox(height: 18),
                _FeatureTile(
                  icon: Icons.balance_rounded,
                  title: 'Grounded answers',
                  body: 'Retrieves relevant BNS sections via Databricks Vector Search (when configured).',
                  scheme: scheme,
                ),
                _FeatureTile(
                  icon: Icons.translate_rounded,
                  title: 'Indic-first',
                  body: 'Built for Hindi + major Indian languages (translation + TTS via Sarvam when keys are set).',
                  scheme: scheme,
                ),
                _FeatureTile(
                  icon: Icons.shield_moon_rounded,
                  title: 'Honest by design',
                  body: 'If the document is unreadable or unrelated, the model is instructed to say so.',
                  scheme: scheme,
                ),
                const SizedBox(height: 18),
                FilledButton.icon(
                  onPressed: () => Navigator.pushNamed(context, AppRoutes.chat),
                  icon: const Icon(Icons.forum_rounded),
                  label: const Padding(
                    padding: EdgeInsets.symmetric(vertical: 14),
                    child: Text('Start'),
                  ),
                ),
                const SizedBox(height: 10),
                Text(
                  'Tip: run the API locally, then `flutter run -d chrome --dart-define=API_BASE=http://localhost:8000`.',
                  style: Theme.of(context).textTheme.bodySmall?.copyWith(color: scheme.onSurfaceVariant),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _FeatureTile extends StatelessWidget {
  const _FeatureTile({
    required this.icon,
    required this.title,
    required this.body,
    required this.scheme,
  });

  final IconData icon;
  final String title;
  final String body;
  final ColorScheme scheme;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: Card(
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Icon(icon, color: scheme.primary),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(title, style: Theme.of(context).textTheme.titleSmall?.copyWith(fontWeight: FontWeight.w800)),
                    const SizedBox(height: 6),
                    Text(body, style: Theme.of(context).textTheme.bodyMedium?.copyWith(height: 1.35)),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
