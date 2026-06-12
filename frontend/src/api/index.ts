import { api } from "./client";
import type {
  Balance,
  Cabinet,
  CalendarLesson,
  ChildCard,
  Comment,
  FinanceSummary,
  Homework,
  Lesson,
  Parent,
  ScheduleSlot,
  Student,
  Transaction,
  User,
} from "./types";

// --- auth ---
export const login = (loginOrEmail: string, password: string) =>
  api.post<User>("/auth/login", { login: loginOrEmail, password }).then((r) => r.data);
export const logout = () => api.post("/auth/logout");
export const fetchMe = () => api.get<User>("/auth/me").then((r) => r.data);
export const changePassword = (current_password: string, new_password: string) =>
  api.post("/auth/change-password", { current_password, new_password });

// --- просмотр от имени (суперюзер) ---
export const impersonationTargets = () =>
  api.get<User[]>("/auth/impersonation/targets").then((r) => r.data);
export const impersonate = (user_id: number) =>
  api.post<User>("/auth/impersonate", { user_id }).then((r) => r.data);
export const stopImpersonation = () =>
  api.post<User>("/auth/impersonate/stop").then((r) => r.data);

// --- admin ---
export const adminListUsers = () => api.get<User[]>("/admin/users").then((r) => r.data);
export const adminCreateUser = (data: {
  email: string;
  login?: string;
  full_name: string;
  role: string;
  password: string;
}) => api.post<User>("/admin/users", data).then((r) => r.data);
export const adminUpdateUser = (id: number, data: Partial<User>) =>
  api.patch<User>(`/admin/users/${id}`, data).then((r) => r.data);
export const adminSetPassword = (id: number, password: string) =>
  api.post(`/admin/users/${id}/password`, { password });
export const adminSendDigest = () => api.post("/admin/digest/send-now");

// --- students (teacher) ---
export const listStudents = () => api.get<Student[]>("/students").then((r) => r.data);
export const createStudent = (data: { email: string; full_name: string }) =>
  api.post<Student>("/students", data).then((r) => r.data);
export const getStudent = (id: number) =>
  api.get<Student>(`/students/${id}`).then((r) => r.data);
export const setStudentPassword = (id: number, password: string) =>
  api.post(`/students/${id}/password`, { password });
export const savePrivateNote = (id: number, teacher_private_note: string | null) =>
  api.patch<Student>(`/students/${id}/private-note`, { teacher_private_note }).then((r) => r.data);

// --- parents (teacher) ---
export const listParents = (studentId: number) =>
  api.get<Parent[]>(`/students/${studentId}/parents`).then((r) => r.data);
export const createParent = (
  studentId: number,
  data: { email: string; full_name: string; lesson_price: string; recommendations?: string },
) => api.post<Parent>(`/students/${studentId}/parents`, data).then((r) => r.data);
export const updateParent = (
  id: number,
  data: { lesson_price?: string; recommendations?: string; full_name?: string },
) => api.patch<Parent>(`/parents/${id}`, data).then((r) => r.data);

// --- lessons (teacher) ---
export const listAllLessons = (from?: string, to?: string) =>
  api
    .get<CalendarLesson[]>("/lessons", { params: { from, to } })
    .then((r) => r.data);
export const listLessons = (studentId: number) =>
  api.get<Lesson[]>(`/students/${studentId}/lessons`).then((r) => r.data);
export const createLesson = (
  studentId: number,
  data: { scheduled_at: string; topic?: string; zoom_link?: string; recommendation?: string },
) => api.post<Lesson>(`/students/${studentId}/lessons`, data).then((r) => r.data);
export const updateLesson = (id: number, data: Partial<Lesson>) =>
  api.patch<Lesson>(`/lessons/${id}`, data).then((r) => r.data);
export const deleteLesson = (id: number) => api.delete(`/lessons/${id}`);
export const conductLesson = (id: number) =>
  api.post<Lesson>(`/lessons/${id}/conduct`).then((r) => r.data);
export const revertLesson = (id: number) =>
  api.post<Lesson>(`/lessons/${id}/revert`).then((r) => r.data);
export const addHomework = (lessonId: number, description: string) =>
  api.post<Homework>(`/lessons/${lessonId}/homeworks`, { description }).then((r) => r.data);
export const updateHomework = (id: number, data: { description?: string; is_done?: boolean }) =>
  api.patch<Homework>(`/homeworks/${id}`, data).then((r) => r.data);
export const deleteHomework = (id: number) => api.delete(`/homeworks/${id}`);

// --- повторяющееся расписание (teacher) ---
export const listSchedule = (studentId: number) =>
  api.get<ScheduleSlot[]>(`/students/${studentId}/schedule`).then((r) => r.data);
export const createScheduleSlot = (studentId: number, weekday: number, start_time: string) =>
  api
    .post<ScheduleSlot>(`/students/${studentId}/schedule`, { weekday, start_time })
    .then((r) => r.data);
export const deleteScheduleSlot = (slotId: number) => api.delete(`/schedule/${slotId}`);

// --- comments ---
export const listComments = (studentId: number) =>
  api.get<Comment[]>(`/students/${studentId}/comments`).then((r) => r.data);
export const addComment = (studentId: number, body: string) =>
  api.post<Comment>(`/students/${studentId}/comments`, { body }).then((r) => r.data);

// --- finance (teacher) ---
export const financeSummary = () =>
  api.get<FinanceSummary>("/finance/summary").then((r) => r.data);
export const listTransactions = (studentId: number) =>
  api.get<Transaction[]>(`/students/${studentId}/transactions`).then((r) => r.data);
export const addPayment = (studentId: number, amount: string, comment?: string) =>
  api.post<Transaction>(`/students/${studentId}/payments`, { amount, comment }).then((r) => r.data);

// --- student cabinet ---
export const fetchCabinet = () => api.get<Cabinet>("/me/cabinet").then((r) => r.data);
export const uploadAvatar = (file: File) => {
  const form = new FormData();
  form.append("file", file);
  return api.post<User>("/me/avatar", form).then((r) => r.data);
};
export const myHomeworks = () => api.get<Homework[]>("/me/homeworks").then((r) => r.data);
export const markHomework = (id: number, is_done: boolean) =>
  api.patch<Homework>(`/me/homeworks/${id}`, { is_done }).then((r) => r.data);
export const myComments = () => api.get<Comment[]>("/me/comments").then((r) => r.data);
export const addMyComment = (body: string) =>
  api.post<Comment>("/me/comments", { body }).then((r) => r.data);

// --- parent ---
export const fetchChild = () => api.get<ChildCard>("/parent/child").then((r) => r.data);
export const fetchBalance = () => api.get<Balance>("/parent/balance").then((r) => r.data);
