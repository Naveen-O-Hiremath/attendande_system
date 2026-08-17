export type UserRole = 'super_admin' | 'admin' | 'teacher' | 'student';
export type UserStatus = 'active' | 'suspended' | 'deleted';
export type EnrollmentStatus = 'pending' | 'approved' | 'rejected' | 'resubmission_requested';

export interface AppUser {
  id: string;
  email: string;
  full_name: string;
  phone: string | null;
  role: UserRole;
  status: UserStatus;
}

export interface FaceEnrollment {
  id: string;
  student_id: string;
  image_urls: string[];
  status: EnrollmentStatus;
  rejection_reason: string | null;
  approved_by: string | null;
  approved_at: string | null;
  created_at: string;
}
