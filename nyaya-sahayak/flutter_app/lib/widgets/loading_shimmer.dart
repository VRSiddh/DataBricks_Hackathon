import 'package:flutter/material.dart';

class LoadingShimmer extends StatefulWidget {
  const LoadingShimmer({super.key});

  @override
  State<LoadingShimmer> createState() => _LoadingShimmerState();
}

class _LoadingShimmerState extends State<LoadingShimmer> with SingleTickerProviderStateMixin {
  late final AnimationController _c = AnimationController(vsync: this, duration: const Duration(milliseconds: 1200))
    ..repeat(reverse: true);

  @override
  void dispose() {
    _c.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: _c,
      builder: (context, _) {
        final t = _c.value;
        return Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: List.generate(
            4,
            (i) => Padding(
              padding: const EdgeInsets.only(bottom: 10),
              child: Container(
                height: 14,
                decoration: BoxDecoration(
                  borderRadius: BorderRadius.circular(8),
                  gradient: LinearGradient(
                    colors: [
                      Colors.white.withValues(alpha: 0.05 + t * 0.08 + i * 0.01),
                      Colors.white.withValues(alpha: 0.18 + t * 0.08),
                    ],
                  ),
                ),
              ),
            ),
          ),
        );
      },
    );
  }
}
