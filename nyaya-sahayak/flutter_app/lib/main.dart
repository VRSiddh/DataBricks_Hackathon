import 'package:flutter/material.dart';

import 'config/routes.dart';
import 'config/theme.dart';

void main() {
  runApp(const NyayaSahayakApp());
}

class NyayaSahayakApp extends StatelessWidget {
  const NyayaSahayakApp({super.key});

  @override
  Widget build(BuildContext context) {
    return ValueListenableBuilder<ThemeMode>(
      valueListenable: nyayaThemeMode,
      builder: (context, mode, _) {
        return MaterialApp(
          title: 'Nyaya-Sahayak',
          debugShowCheckedModeBanner: false,
          theme: AppTheme.light(),
          darkTheme: AppTheme.dark(),
          themeMode: mode,
          initialRoute: AppRoutes.home,
          routes: AppRoutes.routes(),
        );
      },
    );
  }
}
