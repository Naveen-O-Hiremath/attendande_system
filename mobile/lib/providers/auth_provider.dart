import 'package:flutter/foundation.dart';

import '../api/api_client.dart';
import '../api/api_exception.dart';
import '../api/auth_api.dart';
import '../models/user.dart';
import '../services/token_storage.dart';

enum AuthStatus { unknown, authenticated, unauthenticated }

class AuthProvider extends ChangeNotifier {
  final AuthApi _authApi = AuthApi(ApiClient());
  final TokenStorage _tokenStorage = TokenStorage();

  AuthStatus status = AuthStatus.unknown;
  AppUser? currentUser;

  Future<void> bootstrap() async {
    final accessToken = await _tokenStorage.readAccessToken();
    if (accessToken == null) {
      status = AuthStatus.unauthenticated;
      notifyListeners();
      return;
    }

    try {
      currentUser = await _authApi.me(accessToken);
      status = AuthStatus.authenticated;
    } on ApiException catch (e) {
      if (e.statusCode == 401) {
        await _tryRefreshAndFetchMe();
      } else {
        status = AuthStatus.unauthenticated;
      }
    } catch (_) {
      status = AuthStatus.unauthenticated;
    }
    notifyListeners();
  }

  Future<void> _tryRefreshAndFetchMe() async {
    final refreshToken = await _tokenStorage.readRefreshToken();
    if (refreshToken == null) {
      status = AuthStatus.unauthenticated;
      return;
    }
    try {
      final newAccessToken = await _authApi.refresh(refreshToken);
      await _tokenStorage.saveAccessToken(newAccessToken);
      currentUser = await _authApi.me(newAccessToken);
      status = AuthStatus.authenticated;
    } catch (_) {
      await _tokenStorage.clear();
      status = AuthStatus.unauthenticated;
    }
  }

  /// Returns an error message on failure, or null on success.
  Future<String?> login({required String email, required String password}) async {
    try {
      final tokens = await _authApi.login(email: email, password: password);
      await _tokenStorage.save(
        accessToken: tokens.accessToken,
        refreshToken: tokens.refreshToken,
      );
      currentUser = await _authApi.me(tokens.accessToken);
      status = AuthStatus.authenticated;
      notifyListeners();
      return null;
    } on ApiException catch (e) {
      return e.message;
    } catch (_) {
      return 'Could not reach the server. Check your connection and try again.';
    }
  }

  /// Returns an error message on failure, or null on success.
  Future<String?> register({
    required String email,
    required String fullName,
    required String password,
    required String rollNo,
    String? phone,
  }) async {
    try {
      await _authApi.register(
        email: email,
        fullName: fullName,
        password: password,
        rollNo: rollNo,
        phone: phone,
      );
      return null;
    } on ApiException catch (e) {
      return e.message;
    } catch (_) {
      return 'Could not reach the server. Check your connection and try again.';
    }
  }

  Future<void> logout() async {
    await _tokenStorage.clear();
    currentUser = null;
    status = AuthStatus.unauthenticated;
    notifyListeners();
  }
}
