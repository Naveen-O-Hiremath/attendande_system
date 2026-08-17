import 'dart:convert';

import 'package:http/http.dart' as http;

import '../config.dart';
import 'api_exception.dart';

class ApiClient {
  final http.Client _client = http.Client();

  Future<Map<String, dynamic>> get(String path, {String? token}) async {
    final response = await _client.get(
      Uri.parse('$apiBaseUrl$path'),
      headers: _headers(token),
    );
    return _decode(response);
  }

  Future<Map<String, dynamic>> post(
    String path, {
    Map<String, dynamic>? body,
    String? token,
  }) async {
    final response = await _client.post(
      Uri.parse('$apiBaseUrl$path'),
      headers: _headers(token),
      body: body == null ? null : jsonEncode(body),
    );
    return _decode(response);
  }

  Map<String, String> _headers(String? token) => {
        'Content-Type': 'application/json',
        if (token != null) 'Authorization': 'Bearer $token',
      };

  Map<String, dynamic> _decode(http.Response response) {
    final bodyText = response.body.isEmpty ? '{}' : response.body;
    final decoded = jsonDecode(bodyText);

    if (response.statusCode >= 200 && response.statusCode < 300) {
      if (decoded is List) {
        return {'items': decoded};
      }
      return decoded as Map<String, dynamic>;
    }

    throw ApiException(response.statusCode, _extractErrorMessage(decoded));
  }

  String _extractErrorMessage(dynamic decoded) {
    if (decoded is Map && decoded['detail'] != null) {
      final detail = decoded['detail'];
      if (detail is String) return detail;
      if (detail is List && detail.isNotEmpty) {
        final first = detail.first;
        if (first is Map && first['msg'] != null) {
          return first['msg'].toString();
        }
        return first.toString();
      }
      return detail.toString();
    }
    return 'Something went wrong. Please try again.';
  }
}
