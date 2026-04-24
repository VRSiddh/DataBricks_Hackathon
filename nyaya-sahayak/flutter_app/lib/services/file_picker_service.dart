import 'package:file_picker/file_picker.dart';

import '../config/api_config.dart';

class PickedFile {
  PickedFile({required this.name, required this.bytes, required this.mime});

  final String name;
  final List<int> bytes;
  final String mime;
}

class FilePickerService {
  Future<PickedFile?> pickDocument() async {
    final r = await FilePicker.platform.pickFiles(
      type: FileType.custom,
      allowedExtensions: const ['pdf', 'png', 'jpg', 'jpeg', 'webp'],
      withData: true,
    );
    if (r == null || r.files.isEmpty) return null;
    final f = r.files.single;
    if (f.bytes == null) return null;
    final name = f.name;
    final ext = name.split('.').last.toLowerCase();
    final mime = ext == 'pdf'
        ? 'application/pdf'
        : ext == 'png'
            ? 'image/png'
            : (ext == 'jpg' || ext == 'jpeg')
                ? 'image/jpeg'
                : ext == 'webp'
                    ? 'image/webp'
                    : 'application/octet-stream';
    final max = mime == 'application/pdf' ? ApiConfig.maxPdfBytes : ApiConfig.maxImageBytes;
    if (f.bytes!.length > max) {
      throw StateError('File too large. Max ${max ~/ (1024 * 1024)}MB for ${mime.contains('pdf') ? 'PDF' : 'images'}.');
    }
    return PickedFile(name: name, bytes: f.bytes!.toList(), mime: mime);
  }
}
