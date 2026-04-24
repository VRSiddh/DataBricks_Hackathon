import 'package:flutter/material.dart';

import '../models/language.dart';

class LanguageSelector extends StatelessWidget {
  const LanguageSelector({
    super.key,
    required this.value,
    required this.onChanged,
  });

  final String value;
  final ValueChanged<String> onChanged;

  @override
  Widget build(BuildContext context) {
    return InputDecorator(
      decoration: const InputDecoration(
        labelText: 'Response language',
        border: OutlineInputBorder(borderRadius: BorderRadius.all(Radius.circular(16))),
      ),
      child: DropdownButtonHideUnderline(
        child: DropdownButton<String>(
          value: value,
          isExpanded: true,
          items: [
            for (final l in AppLanguage.supported)
              DropdownMenuItem(value: l.code, child: Text(l.label)),
          ],
          onChanged: (v) {
            if (v != null) onChanged(v);
          },
        ),
      ),
    );
  }
}
