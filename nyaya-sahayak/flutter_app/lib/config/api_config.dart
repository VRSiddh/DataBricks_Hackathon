/// Set at build time: `flutter run --dart-define=API_BASE=https://your-app.cloud.databricks.com`
class ApiConfig {
  static const String baseUrl = String.fromEnvironment(
    'API_BASE',
    defaultValue: 'http://localhost:8000',
  );

  static const int maxImageBytes = 5 * 1024 * 1024;
  static const int maxPdfBytes = 8 * 1024 * 1024;
}
