import 'package:flutter/material.dart';

import '../screens/chat_screen.dart';
import '../screens/home_screen.dart';

class AppRoutes {
  static const home = '/';
  static const chat = '/chat';

  static Map<String, WidgetBuilder> routes() => {
        home: (_) => const HomeScreen(),
        chat: (_) => const ChatScreen(),
      };
}
