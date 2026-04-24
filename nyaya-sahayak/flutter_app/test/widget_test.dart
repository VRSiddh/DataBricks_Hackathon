import 'package:flutter_test/flutter_test.dart';
import 'package:nyaya_sahayak/main.dart';

void main() {
  testWidgets('App boots', (tester) async {
    await tester.pumpWidget(const NyayaSahayakApp());
    expect(find.text('Nyaya-Sahayak'), findsOneWidget);
  });
}
