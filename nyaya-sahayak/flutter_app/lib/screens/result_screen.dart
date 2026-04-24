import 'package:flutter/material.dart';

import '../models/analysis_result.dart';

class ResultScreen extends StatelessWidget {
  const ResultScreen({super.key, required this.result});

  final AnalysisResult result;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Analysis')),
      body: ListView(
        padding: const EdgeInsets.all(18),
        children: [
          Text('Summary', style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w900)),
          const SizedBox(height: 8),
          SelectableText(result.documentSummary),
          const SizedBox(height: 18),
          Text('Advice', style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w900)),
          const SizedBox(height: 8),
          SelectableText(result.advice),
        ],
      ),
    );
  }
}
