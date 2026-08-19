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

export interface SchoolClass {
  id: string;
  name: string;
  section: string | null;
  year: string | null;
  student_count: number;
}

export interface StudentSummary {
  id: string;
  email: string;
  full_name: string;
  roll_no: string;
  enrollment_status: EnrollmentStatus;
  school_class_id: string | null;
  school_class_name: string | null;
}

export interface AnnouncementComment {
  id: string;
  user_id: string;
  author_name: string;
  body: string;
  created_at: string;
}

export interface Announcement {
  id: string;
  title: string;
  body: string;
  created_by: string;
  author_name: string;
  created_at: string;
  like_count: number;
  comment_count: number;
  liked_by_me: boolean;
  comments: AnnouncementComment[];
}

export interface AttendanceRecord {
  id: string;
  student_id: string;
  student_name: string;
  roll_no: string;
  school_class_id: string;
  school_class_name: string;
  marked_at: string;
  status: string;
  method: string;
  geo_verified: boolean;
  match_confidence: number | null;
  device_id: string | null;
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
