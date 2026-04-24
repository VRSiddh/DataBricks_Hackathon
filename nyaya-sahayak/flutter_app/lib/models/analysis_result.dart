class AnalysisResult {
  final String documentSummary;
  final String advice;
  final List<String> actionSteps;
  final List<Map<String, dynamic>> relevantSections;
  final List<Map<String, dynamic>> ipcMapping;
  final String? audioBase64;
  final String? sessionId;
  final String? ocrMethod;
  final double? latencySec;
  final String? documentTextPreview;

  AnalysisResult({
    required this.documentSummary,
    required this.advice,
    required this.actionSteps,
    required this.relevantSections,
    required this.ipcMapping,
    this.audioBase64,
    this.sessionId,
    this.ocrMethod,
    this.latencySec,
    this.documentTextPreview,
  });

  factory AnalysisResult.fromJson(Map<String, dynamic> json) {
    final a = json['analysis'] as Map<String, dynamic>? ?? {};
    return AnalysisResult(
      documentSummary: (a['document_summary'] ?? '').toString(),
      advice: (a['advice'] ?? '').toString(),
      actionSteps: List<String>.from(a['action_steps'] ?? const []),
      relevantSections: List<Map<String, dynamic>>.from(
        (a['relevant_sections'] as List?)?.map((e) => Map<String, dynamic>.from(e as Map)) ?? const [],
      ),
      ipcMapping: List<Map<String, dynamic>>.from(
        (a['ipc_mapping'] as List?)?.map((e) => Map<String, dynamic>.from(e as Map)) ?? const [],
      ),
      audioBase64: json['audio_base64'] as String?,
      sessionId: json['session_id'] as String?,
      ocrMethod: a['ocr_method'] as String?,
      latencySec: (json['latency_sec'] as num?)?.toDouble(),
      documentTextPreview: a['document_text_preview'] as String?,
    );
  }
}
