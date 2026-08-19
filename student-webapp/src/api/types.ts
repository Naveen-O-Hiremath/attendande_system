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

export interface FaceMatchResult {
  matched: boolean;
  needs_review: boolean;
  similarity: number;
  attendance_record_id: string | null;
  message: string;
}
