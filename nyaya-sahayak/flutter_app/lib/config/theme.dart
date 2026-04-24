import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

/// Toggle from anywhere: `nyayaThemeMode.value = ThemeMode.dark`.
final ValueNotifier<ThemeMode> nyayaThemeMode = ValueNotifier<ThemeMode>(ThemeMode.light);

class AppTheme {
  static ThemeData light() {
    final base = ThemeData(
      useMaterial3: true,
      colorScheme: ColorScheme.fromSeed(
        seedColor: const Color(0xFF1B4D3E),
        brightness: Brightness.light,
        surface: const Color(0xFFF7F9F8),
      ),
      scaffoldBackgroundColor: const Color(0xFFF2F6F4),
    );
    return base.copyWith(
      textTheme: GoogleFonts.plusJakartaSansTextTheme(base.textTheme),
      appBarTheme: const AppBarTheme(centerTitle: true, elevation: 0),
      cardTheme: CardThemeData(
        elevation: 0,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
        color: Colors.white.withValues(alpha: 0.85),
      ),
    );
  }

  static ThemeData dark() {
    final base = ThemeData(
      useMaterial3: true,
      colorScheme: ColorScheme.fromSeed(
        seedColor: const Color(0xFF4FD1C5),
        brightness: Brightness.dark,
        surface: const Color(0xFF0F172A),
      ),
      scaffoldBackgroundColor: const Color(0xFF0B1220),
    );
    return base.copyWith(
      textTheme: GoogleFonts.plusJakartaSansTextTheme(base.textTheme),
      appBarTheme: const AppBarTheme(centerTitle: true, elevation: 0),
      cardTheme: CardThemeData(
        elevation: 0,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
        color: const Color(0xFF111827).withValues(alpha: 0.9),
      ),
    );
  }
}
