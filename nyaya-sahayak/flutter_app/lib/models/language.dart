class AppLanguage {
  final String code;
  final String label;

  const AppLanguage(this.code, this.label);

  static const List<AppLanguage> supported = [
    AppLanguage('en-IN', 'English'),
    AppLanguage('hi-IN', 'Hindi'),
    AppLanguage('mr-IN', 'Marathi'),
    AppLanguage('ta-IN', 'Tamil'),
    AppLanguage('te-IN', 'Telugu'),
    AppLanguage('kn-IN', 'Kannada'),
    AppLanguage('ml-IN', 'Malayalam'),
    AppLanguage('bn-IN', 'Bengali'),
    AppLanguage('gu-IN', 'Gujarati'),
    AppLanguage('pa-IN', 'Punjabi'),
    AppLanguage('od-IN', 'Odia'),
  ];
}
