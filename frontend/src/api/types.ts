export type Role = "superuser" | "teacher" | "student" | "parent";

export interface User {
  id: number;
  email: string;
  login: string;
  full_name: string;
  role: Role;
  avatar_path: string | null;
  is_active: boolean;
  created_at: string;
  /** true — суперюзер смотрит систему от имени этого пользователя */
  impersonating?: boolean;
}

export interface Student {
  id: number;
  user: User;
  created_at: string;
  teacher_private_note?: string | null;
  default_zoom_link?: string | null;
  birthday?: string | null;
}

export interface Parent {
  id: number;
  student_id: number;
  user: User;
  lesson_price: string;
  recommendations: string | null;
  created_at: string;
}

export type LessonStatus = "planned" | "conducted" | "cancelled";

export interface HomeworkAttachment {
  id: number;
  homework_id: number;
  name: string;
  file_path: string | null;
  url: string | null;
}

export interface LessonAttachment {
  id: number;
  lesson_id: number;
  name: string;
  file_path: string | null;
  url: string | null;
}

export interface Homework {
  id: number;
  lesson_id: number;
  description: string;
  is_done: boolean;
  student_answer: string | null;
  checked_at: string | null;
  grade: number | null;
  attachments: HomeworkAttachment[];
  created_at: string;
}

export type CancellationKind = "teacher" | "student" | "late";

export interface Lesson {
  id: number;
  student_id: number;
  scheduled_at: string;
  duration_minutes: number;
  price: string | null;
  topic: string | null;
  zoom_link: string | null;
  recommendation: string | null;
  status: LessonStatus;
  conducted_at: string | null;
  cancellation_kind: CancellationKind | null;
  cancellation_comment: string | null;
  rescheduled_from: string | null;
  homeworks: Homework[];
  attachments: LessonAttachment[];
}

export interface CalendarLesson extends Lesson {
  student_name: string;
}

export interface EmailSettings {
  backend: "console" | "smtp";
  smtp_host: string;
  smtp_port: number;
  smtp_user: string;
  smtp_from: string;
  password_set: boolean;
}

export interface EmailLogEntry {
  id: number;
  to_email: string;
  subject: string;
  status: "sent" | "error";
  error: string | null;
  created_at: string;
}

export interface Card {
  id: number;
  set_id: number;
  front: string;
  back: string;
  position: number;
  times_correct: number;
  times_wrong: number;
}

export interface CardSet {
  id: number;
  student_id: number;
  title: string;
  cards: Card[];
}

export interface CardSetSummary {
  id: number;
  student_id: number;
  title: string;
  total: number;
  learned: number;
}

export interface ScheduleSlot {
  id: number;
  student_id: number;
  weekday: number; // 0=Пн … 6=Вс
  start_time: string; // "16:00:00"
}

export interface Transaction {
  id: number;
  student_id: number;
  type: "charge" | "payment";
  amount: string;
  lesson_id: number | null;
  comment: string | null;
  created_at: string;
}

export interface StudentFinance {
  student_id: number;
  student_name: string;
  earned: string;
  paid: string;
  debt: string;
  lesson_price: string;
}

export interface FinanceSummary {
  total_earned: string;
  students: StudentFinance[];
}

export interface Balance {
  lesson_price: string;
  charged: string;
  paid: string;
  debt: string;
  transactions: Transaction[];
}

export interface Comment {
  id: number;
  student_id: number;
  author_user_id: number;
  author_name: string;
  body: string;
  created_at: string;
}

export interface Cabinet {
  user: User;
  lessons: Lesson[];
}

export interface ChildCard {
  student: User;
  lesson_price: string;
  recommendations: string | null;
  lessons: Lesson[];
}
