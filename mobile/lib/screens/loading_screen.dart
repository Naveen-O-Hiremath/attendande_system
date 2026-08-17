import 'package:flutter/material.dart';

import '../theme.dart';

/// In-app loading screen shown while the Flutter engine checks for a stored
/// session (the native splash screen covers the earlier cold-start gap).
class LoadingScreen extends StatelessWidget {
  const LoadingScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.white,
      body: Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            ClipRRect(
              borderRadius: BorderRadius.circular(28),
              child: Image.asset(
                'assets/icon/app_icon.png',
                width: 120,
                height: 120,
              ),
            ),
            const SizedBox(height: 24),
            const SizedBox(
              width: 28,
              height: 28,
              child: CircularProgressIndicator(
                strokeWidth: 3,
                color: AppColors.purple,
              ),
            ),
            const SizedBox(height: 16),
            Text(
              'Loading…',
              style: TextStyle(color: Colors.grey.shade600, fontSize: 14),
            ),
          ],
        ),
      ),
    );
  }
}
