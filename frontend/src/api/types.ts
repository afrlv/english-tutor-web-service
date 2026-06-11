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

export interface Homework {
  id: number;
  lesson_id: number;
  description: string;
  is_done: boolean;
  created_at: string;
}

export interface Lesson {
  id: number;
  student_id: number;
  scheduled_at: string;
  topic: string | null;
  zoom_link: string | null;
  recommendation: string | null;
  status: LessonStatus;
  conducted_at: string | null;
  homeworks: Homework[];
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
