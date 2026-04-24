import 'package:flutter/material.dart';

import '../config/theme.dart';
import '../models/analysis_result.dart';
import '../models/chat_message.dart';
import '../services/api_service.dart';
import '../services/audio_service.dart';
import '../services/file_picker_service.dart';
import '../widgets/audio_player_widget.dart';
import '../widgets/document_upload.dart';
import '../widgets/language_selector.dart';
import '../widgets/loading_shimmer.dart';
import '../widgets/message_bubble.dart';

class ChatScreen extends StatefulWidget {
  const ChatScreen({super.key});

  @override
  State<ChatScreen> createState() => _ChatScreenState();
}

class _ChatScreenState extends State<ChatScreen> {
  final _api = ApiService();
  final _picker = FilePickerService();
  final _audio = AudioService();
  final _scroll = ScrollController();
  final _followUp = TextEditingController();

  String _lang = 'hi-IN';
  bool _busy = false;
  String? _sessionId;
  String? _docPreview;

  final List<ChatMessage> _msgs = [];

  @override
  void dispose() {
    _scroll.dispose();
    _followUp.dispose();
    _audio.stop();
    super.dispose();
  }

  Future<void> _pickAndAnalyze() async {
    setState(() => _busy = true);
    try {
      final picked = await _picker.pickDocument();
      if (!mounted) return;
      if (picked == null) {
        setState(() => _busy = false);
        return;
      }

      _msgs.add(ChatMessage(role: MessageRole.user, text: 'Uploaded document for analysis.', attachmentName: picked.name));
      setState(() {});

      final res = await _api.analyze(
        fileBytes: picked.bytes,
        fileName: picked.name,
        mimeType: picked.mime,
        language: _lang,
      );

      _sessionId = res.sessionId;
      _docPreview = res.documentTextPreview;

      final buf = StringBuffer()
        ..writeln(res.documentSummary)
        ..writeln()
        ..writeln(res.advice);

      if (res.actionSteps.isNotEmpty) {
        buf.writeln('\nNext steps:');
        for (var i = 0; i < res.actionSteps.length; i++) {
          buf.writeln('${i + 1}. ${res.actionSteps[i]}');
        }
      }

      _msgs.add(ChatMessage(role: MessageRole.assistant, text: buf.toString()));
      setState(() => _busy = false);
      _scrollToEnd();

      if (!mounted) return;
      await _maybeOfferDetails(res);
    } catch (e) {
      if (!mounted) return;
      _msgs.add(ChatMessage(role: MessageRole.assistant, text: 'Something went wrong:\n$e'));
      setState(() => _busy = false);
      _scrollToEnd();
    }
  }

  Future<void> _maybeOfferDetails(AnalysisResult res) async {
    await showModalBottomSheet<void>(
      context: context,
      showDragHandle: true,
      isScrollControlled: true,
      builder: (context) {
        return Padding(
          padding: EdgeInsets.only(left: 16, right: 16, top: 8, bottom: 16 + MediaQuery.of(context).viewInsets.bottom),
          child: SingleChildScrollView(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text('Sections retrieved', style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w900)),
                const SizedBox(height: 10),
                if (res.relevantSections.isEmpty)
                  Text('No vector hits returned (check Vector Search + endpoint config).', style: Theme.of(context).textTheme.bodyMedium)
                else
                  ...res.relevantSections.map(
                    (h) => ListTile(
                      dense: true,
                      title: Text('Section ${h['section'] ?? ''} — ${h['name'] ?? ''}'),
                      subtitle: Text('score: ${h['relevance'] ?? 'n/a'}'),
                    ),
                  ),
                const Divider(height: 28),
                Text('IPC hints', style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w900)),
                const SizedBox(height: 10),
                if (res.ipcMapping.isEmpty)
                  const Text('None detected.')
                else
                  ...res.ipcMapping.map(
                    (m) => ListTile(
                      dense: true,
                      title: Text('IPC ${m['ipc_section']} → BNS ${m['bns_section']}'),
                      subtitle: Text((m['note'] ?? '').toString()),
                    ),
                  ),
                const SizedBox(height: 10),
                Row(
                  children: [
                    AudioPlayerWidget(enabled: (res.audioBase64 ?? '').isNotEmpty, onPlay: () => _audio.playBase64(res.audioBase64)),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Text(
                        'OCR: ${res.ocrMethod ?? 'n/a'} • ${(res.latencySec ?? 0).toStringAsFixed(2)}s',
                        style: Theme.of(context).textTheme.bodySmall,
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ),
        );
      },
    );
  }

  void _scrollToEnd() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (!_scroll.hasClients) return;
      _scroll.animateTo(
        _scroll.position.maxScrollExtent,
        duration: const Duration(milliseconds: 350),
        curve: Curves.easeOutCubic,
      );
    });
  }

  Future<void> _sendFollowUp() async {
    final text = _followUp.text.trim();
    if (text.isEmpty || _sessionId == null) return;

    setState(() => _busy = true);
    _msgs.add(ChatMessage(role: MessageRole.user, text: text));
    _followUp.clear();
    setState(() {});
    _scrollToEnd();

    try {
      final reply = await _api.chat(
        sessionId: _sessionId!,
        message: text,
        language: _lang,
        documentContext: _docPreview,
      );
      _msgs.add(ChatMessage(role: MessageRole.assistant, text: reply));
    } catch (e) {
      _msgs.add(ChatMessage(role: MessageRole.assistant, text: 'Chat error:\n$e'));
    } finally {
      if (mounted) setState(() => _busy = false);
      _scrollToEnd();
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Nyaya chat'),
        actions: [
          IconButton(
            tooltip: 'Toggle brightness',
            onPressed: () {
              nyayaThemeMode.value = nyayaThemeMode.value == ThemeMode.dark ? ThemeMode.light : ThemeMode.dark;
            },
            icon: const Icon(Icons.brightness_6_rounded),
          ),
        ],
      ),
      body: Column(
        children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 12, 16, 8),
            child: LanguageSelector(value: _lang, onChanged: (v) => setState(() => _lang = v)),
          ),
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16),
            child: DocumentUploadCard(busy: _busy, onPick: _pickAndAnalyze),
          ),
          const SizedBox(height: 10),
          Expanded(
            child: Stack(
              children: [
                ListView.builder(
                  controller: _scroll,
                  padding: const EdgeInsets.fromLTRB(16, 8, 16, 16),
                  itemCount: _msgs.length + (_busy ? 1 : 0),
                  itemBuilder: (context, i) {
                    if (_busy && i == _msgs.length) {
                      return const Padding(
                        padding: EdgeInsets.only(top: 10),
                        child: LoadingShimmer(),
                      );
                    }
                    return MessageBubble(message: _msgs[i]);
                  },
                ),
              ],
            ),
          ),
          SafeArea(
            top: false,
            child: Padding(
              padding: const EdgeInsets.fromLTRB(12, 0, 12, 12),
              child: Row(
                children: [
                  Expanded(
                    child: TextField(
                      controller: _followUp,
                      minLines: 1,
                      maxLines: 4,
                      decoration: const InputDecoration(
                        hintText: 'Follow-up question (after first analysis)…',
                        border: OutlineInputBorder(borderRadius: BorderRadius.all(Radius.circular(18))),
                      ),
                      onSubmitted: (_) => _sendFollowUp(),
                    ),
                  ),
                  const SizedBox(width: 10),
                  FilledButton(
                    onPressed: (_busy || _sessionId == null) ? null : _sendFollowUp,
                    child: const Icon(Icons.send_rounded),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}
