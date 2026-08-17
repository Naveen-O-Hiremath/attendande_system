import '../models/user.dart';
import 'api_client.dart';

class AuthTokens {
  final String accessToken;
  final String refreshToken;

  AuthTokens({required this.accessToken, required this.refreshToken});
}

class AuthApi {
  final ApiClient _client;

  AuthApi(this._client);

  Future<AppUser> register({
    required String email,
    required String fullName,
    required String password,
    required String rollNo,
    String? phone,
  }) async {
    final json = await _client.post('/auth/register', body: {
      'email': email,
      'full_name': fullName,
      'password': password,
      'roll_no': rollNo,
      if (phone != null && phone.isNotEmpty) 'phone': phone,
    });
    return AppUser.fromJson(json);
  }

  Future<AuthTokens> login({required String email, required String password}) async {
    final json = await _client.post('/auth/login', body: {
      'email': email,
      'password': password,
    });
    return AuthTokens(
      accessToken: json['access_token'] as String,
      refreshToken: json['refresh_token'] as String,
    );
  }

  Future<AppUser> me(String accessToken) async {
    final json = await _client.get('/auth/me', token: accessToken);
    return AppUser.fromJson(json);
  }

  Future<String> refresh(String refreshToken) async {
    final json = await _client.post('/auth/refresh', body: {
      'refresh_token': refreshToken,
    });
    return json['access_token'] as String;
  }
}
