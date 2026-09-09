import 'package:flutter_test/flutter_test.dart';
import 'package:wallcraft_mobile/main.dart';

void main() {
  testWidgets('Wallcraft app boots', (WidgetTester tester) async {
    await tester.pumpWidget(const WallcraftApp());
    expect(find.text('Wallcraft'), findsOneWidget);
  });
}
