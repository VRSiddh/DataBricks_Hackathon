import 'dart:convert';

import 'package:http/http.dart' as http;
import 'package:http_parser/http_parser.dart';

import '../config/api_config.dart';
import '../models/analysis_result.dart';

class ApiService {
  ApiService({String? baseUrl}) : _base = baseUrl ?? ApiConfig.baseUrl;

  final String _base;

  Future<AnalysisResult> analyze({
    required List<int> fileBytes,
    required String fileName,
    required String mimeType,
    required String language,
    String? query,
  }) async {
    final uri = Uri.parse('$_base/api/analyze_upload');
    final req = http.MultipartRequest('POST', uri)
      ..fields['language'] = language
      ..files.add(
        http.MultipartFile.fromBytes(
          'file',
          fileBytes,
          filename: fileName,
          contentType: MediaType.parse(mimeType),
        ),
      );
    if (query != null && query.isNotEmpty) {
      req.fields['query'] = query;
    }
    final streamed = await req.send().timeout(const Duration(seconds: 120));
    final body = await streamed.stream.bytesToString();
    if (streamed.statusCode >= 400) {
      throw ApiException(streamed.statusCode, body);
    }
    final map = json.decode(body) as Map<String, dynamic>;
    return AnalysisResult.fromJson(map);
  }

  Future<String> chat({
    required String sessionId,
    required String message,
    required String language,
    String? documentContext,
  }) async {
    final uri = Uri.parse('$_base/api/chat');
    final res = await http
        .post(
          uri,
          headers: {'Content-Type': 'application/json'},
          body: json.encode({
            'session_id': sessionId,
            'message': message,
            'language': language,
            'document_context': documentContext,
          }),
        )
        .timeout(const Duration(seconds: 120));
    if (res.statusCode >= 400) {
      throw ApiException(res.statusCode, res.body);
    }
    final map = json.decode(res.body) as Map<String, dynamic>;
    return (map['reply'] ?? '').toString();
  }
}

class ApiException implements Exception {
  ApiException(this.status, this.body);
  final int status;
  final String body;
  @override
  String toString() => 'ApiException($status): $body';
}
