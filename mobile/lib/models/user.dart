class AppUser {
  final String id;
  final String email;
  final String fullName;
  final String? phone;
  final String role;
  final String status;

  AppUser({
    required this.id,
    required this.email,
    required this.fullName,
    required this.phone,
    required this.role,
    required this.status,
  });

  factory AppUser.fromJson(Map<String, dynamic> json) => AppUser(
        id: json['id'] as String,
        email: json['email'] as String,
        fullName: json['full_name'] as String,
        phone: json['phone'] as String?,
        role: json['role'] as String,
        status: json['status'] as String,
      );

  bool get isStudent => role == 'student';
}
