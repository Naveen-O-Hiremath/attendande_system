import 'package:flutter_test/flutter_test.dart';

import 'package:attendance_app/main.dart';
import 'package:attendance_app/screens/loading_screen.dart';

void main() {
  testWidgets('App boots into the loading screen before auth status resolves',
      (WidgetTester tester) async {
    await tester.pumpWidget(const AttendanceApp());
    expect(find.byType(LoadingScreen), findsOneWidget);
  });
}
