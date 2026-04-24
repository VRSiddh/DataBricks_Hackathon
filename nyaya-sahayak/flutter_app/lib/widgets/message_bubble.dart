import 'package:flutter/material.dart';

import '../models/chat_message.dart';

class MessageBubble extends StatelessWidget {
  const MessageBubble({super.key, required this.message});

  final ChatMessage message;

  @override
  Widget build(BuildContext context) {
    final isUser = message.role == MessageRole.user;
    final scheme = Theme.of(context).colorScheme;
    final align = isUser ? Alignment.centerRight : Alignment.centerLeft;
    final bg = isUser ? scheme.primaryContainer : scheme.surfaceContainerHighest.withValues(alpha: 0.65);
    final fg = isUser ? scheme.onPrimaryContainer : scheme.onSurface;
    return Align(
      alignment: align,
      child: ConstrainedBox(
        constraints: const BoxConstraints(maxWidth: 720),
        child: Container(
          margin: const EdgeInsets.symmetric(vertical: 6),
          padding: const EdgeInsets.all(14),
          decoration: BoxDecoration(
            color: bg,
            borderRadius: BorderRadius.only(
              topLeft: const Radius.circular(18),
              topRight: const Radius.circular(18),
              bottomLeft: Radius.circular(isUser ? 18 : 4),
              bottomRight: Radius.circular(isUser ? 4 : 18),
            ),
            border: Border.all(color: scheme.outlineVariant.withValues(alpha: 0.25)),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              if (message.attachmentName != null)
                Padding(
                  padding: const EdgeInsets.only(bottom: 8),
                  child: Row(
                    children: [
                      const Icon(Icons.attach_file_rounded, size: 18),
                      const SizedBox(width: 6),
                      Expanded(
                        child: Text(
                          message.attachmentName!,
                          style: TextStyle(color: fg, fontWeight: FontWeight.w600),
                          overflow: TextOverflow.ellipsis,
                        ),
                      ),
                    ],
                  ),
                ),
              SelectableText(message.text, style: TextStyle(color: fg, height: 1.35)),
            ],
          ),
        ),
      ),
    );
  }
}
