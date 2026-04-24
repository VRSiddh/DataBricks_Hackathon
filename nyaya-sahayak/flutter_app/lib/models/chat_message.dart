enum MessageRole { user, assistant, system }

class ChatMessage {
  final MessageRole role;
  final String text;
  final String? attachmentName;

  ChatMessage({required this.role, required this.text, this.attachmentName});
}
