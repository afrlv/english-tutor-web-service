import { api } from "./client";
import type {
  Balance,
  Cabinet,
  CalendarLesson,
  Card,
  CardSet,
  CardSetSummary,
  ChildCard,
  Comment,
  EmailLogEntry,
  EmailSettings,
  DashboardStats,
  FinanceSummary,
  Homework,
  HomeworkAttachment,
  Lesson,
  LessonAttachment,
  Parent,
  ParentOverview,
  TeacherParent,
  Progress,
  ScheduleSlot,
  Student,
  UnassignedStudent,
  StudyDirection,
  StudyToday,
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
export const adminDeleteUser = (id: number) => api.delete(`/admin/users/${id}`);
export const adminListDeletedUsers = () =>
  api.get<User[]>("/admin/users/deleted").then((r) => r.data);
export const adminRestoreUser = (id: number) =>
  api.post<User>(`/admin/users/${id}/restore`).then((r) => r.data);
export const adminSendDigest = () => api.post("/admin/digest/send-now");
export const getEmailSettings = () =>
  api.get<EmailSettings>("/admin/email-settings").then((r) => r.data);
export const saveEmailSettings = (data: {
  backend: string;
  smtp_host: string;
  smtp_port: number;
  smtp_user: string;
  smtp_from: string;
  smtp_password: string | null;
}) => api.put<EmailSettings>("/admin/email-settings", data).then((r) => r.data);
export const sendTestEmail = () =>
  api.post<{ ok: boolean }>("/admin/email-settings/test").then((r) => r.data);
export const listEmailLog = () =>
  api.get<EmailLogEntry[]>("/admin/email-log").then((r) => r.data);

// --- students (teacher) ---
export const listStudents = () => api.get<Student[]>("/students").then((r) => r.data);
export const createStudent = (data: { email: string; full_name: string }) =>
  api.post<Student>("/students", data).then((r) => r.data);
export const listUnassignedStudents = () =>
  api.get<UnassignedStudent[]>("/students-unassigned").then((r) => r.data);
export const attachStudent = (user_id: number) =>
  api.post<Student>("/students/attach", { user_id }).then((r) => r.data);
export const assignTeacher = (userId: number, teacher_id: number) =>
  api.post(`/admin/users/${userId}/assign-teacher`, { teacher_id });
export const getStudent = (id: number) =>
  api.get<Student>(`/students/${id}`).then((r) => r.data);
export const updateStudent = (
  id: number,
  data: { full_name?: string; default_zoom_link?: string | null; birthday?: string | null },
) => api.patch<Student>(`/students/${id}`, data).then((r) => r.data);
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
export interface LessonInput {
  scheduled_at: string;
  duration_minutes?: number;
  price?: string | null;
  topic?: string;
  zoom_link?: string;
  recommendation?: string;
}

export const createLesson = (studentId: number, data: LessonInput) =>
  api.post<Lesson>(`/students/${studentId}/lessons`, data).then((r) => r.data);
export const updateLesson = (id: number, data: Partial<Lesson> | LessonInput) =>
  api.patch<Lesson>(`/lessons/${id}`, data).then((r) => r.data);
export const deleteLesson = (id: number) => api.delete(`/lessons/${id}`);
export const conductLesson = (id: number) =>
  api.post<Lesson>(`/lessons/${id}/conduct`).then((r) => r.data);
export const revertLesson = (id: number) =>
  api.post<Lesson>(`/lessons/${id}/revert`).then((r) => r.data);
export const cancelLesson = (
  id: number,
  kind: string,
  comment: string | null,
  charge_amount: string | null,
) =>
  api
    .post<Lesson>(`/lessons/${id}/cancel`, { kind, comment, charge_amount })
    .then((r) => r.data);
export const restoreLesson = (id: number) =>
  api.post<Lesson>(`/lessons/${id}/restore`).then((r) => r.data);
export const addHomework = (lessonId: number, description: string) =>
  api.post<Homework>(`/lessons/${lessonId}/homeworks`, { description }).then((r) => r.data);
export const updateHomework = (
  id: number,
  data: { description?: string; is_done?: boolean; is_checked?: boolean; grade?: number },
) => api.patch<Homework>(`/homeworks/${id}`, data).then((r) => r.data);
export const deleteHomework = (id: number) => api.delete(`/homeworks/${id}`);
export const uploadHomeworkFile = (homeworkId: number, file: File) => {
  const form = new FormData();
  form.append("file", file);
  return api
    .post<HomeworkAttachment>(`/homeworks/${homeworkId}/attachments`, form)
    .then((r) => r.data);
};
export const addHomeworkLink = (homeworkId: number, url: string, name?: string) =>
  api
    .post<HomeworkAttachment>(`/homeworks/${homeworkId}/attachments/link`, { url, name })
    .then((r) => r.data);
export const deleteAttachment = (id: number) => api.delete(`/attachments/${id}`);
// материалы урока
export const getLessonDetail = (id: number) =>
  api.get<CalendarLesson>(`/lessons/${id}`).then((r) => r.data);
export const uploadLessonFile = (lessonId: number, file: File) => {
  const form = new FormData();
  form.append("file", file);
  return api
    .post<LessonAttachment>(`/lessons/${lessonId}/attachments`, form)
    .then((r) => r.data);
};
export const addLessonLink = (lessonId: number, url: string, name?: string) =>
  api
    .post<LessonAttachment>(`/lessons/${lessonId}/attachments/link`, { url, name })
    .then((r) => r.data);
export const deleteLessonAttachment = (id: number) =>
  api.delete(`/lesson-attachments/${id}`);
// карточка урока ученика
export const myLesson = (id: number) =>
  api.get<Lesson>(`/me/lessons/${id}`).then((r) => r.data);

// --- повторяющееся расписание (teacher) ---
export const listSchedule = (studentId: number) =>
  api.get<ScheduleSlot[]>(`/students/${studentId}/schedule`).then((r) => r.data);
export const createScheduleSlot = (studentId: number, weekday: number, start_time: string) =>
  api
    .post<ScheduleSlot>(`/students/${studentId}/schedule`, { weekday, start_time })
    .then((r) => r.data);
export const deleteScheduleSlot = (slotId: number) => api.delete(`/schedule/${slotId}`);

// --- карточки (наборы слов) ---
export const listCardSets = (studentId: number) =>
  api.get<CardSetSummary[]>(`/students/${studentId}/card-sets`).then((r) => r.data);
export const createCardSet = (
  studentId: number,
  title: string,
  cards: { front: string; back: string; example?: string | null }[],
) => api.post<CardSet>(`/students/${studentId}/card-sets`, { title, cards }).then((r) => r.data);
// наборы конкретного урока
export const listLessonCardSets = (lessonId: number) =>
  api.get<CardSetSummary[]>(`/lessons/${lessonId}/card-sets`).then((r) => r.data);
export const createLessonCardSet = (lessonId: number, title: string) =>
  api.post<CardSet>(`/lessons/${lessonId}/card-sets`, { title, cards: [] }).then((r) => r.data);
export const myLessonCardSets = (lessonId: number) =>
  api.get<CardSetSummary[]>(`/me/lessons/${lessonId}/card-sets`).then((r) => r.data);
export const getCardSet = (setId: number) =>
  api.get<CardSet>(`/card-sets/${setId}`).then((r) => r.data);
export const renameCardSet = (setId: number, title: string) =>
  api.patch<CardSet>(`/card-sets/${setId}`, { title }).then((r) => r.data);
export const deleteCardSet = (setId: number) => api.delete(`/card-sets/${setId}`);
export const copyCardSet = (setId: number) =>
  api.post<CardSet>(`/card-sets/${setId}/copy`).then((r) => r.data);
export const attachCardSetToLesson = (lessonId: number, setId: number) =>
  api.post<CardSet>(`/lessons/${lessonId}/card-sets/${setId}/attach`).then((r) => r.data);
export const addCard = (
  setId: number,
  front: string,
  back: string,
  example: string | null = null,
) => api.post<Card>(`/card-sets/${setId}/cards`, { front, back, example }).then((r) => r.data);
export const updateCard = (
  cardId: number,
  front: string,
  back: string,
  example: string | null = null,
) => api.patch<Card>(`/cards/${cardId}`, { front, back, example }).then((r) => r.data);
export const deleteCard = (cardId: number) => api.delete(`/cards/${cardId}`);
// сторона ученика
export const myCardSets = () =>
  api.get<CardSetSummary[]>("/me/card-sets").then((r) => r.data);
export const myCardSet = (setId: number) =>
  api.get<CardSet>(`/me/card-sets/${setId}`).then((r) => r.data);
export const answerCard = (cardId: number, correct: boolean) =>
  api.post<Card>(`/me/cards/${cardId}/answer`, { correct }).then((r) => r.data);
export const studySet = (setId: number, direction: StudyDirection) =>
  api
    .get<Card[]>(`/me/card-sets/${setId}/study`, { params: { direction } })
    .then((r) => r.data);
export const studyToday = () =>
  api.get<StudyToday>("/me/study/today").then((r) => r.data);
export const getProgress = () =>
  api.get<Progress>("/me/progress").then((r) => r.data);

// --- comments ---
export const listComments = (studentId: number) =>
  api.get<Comment[]>(`/students/${studentId}/comments`).then((r) => r.data);
export const addComment = (studentId: number, body: string) =>
  api.post<Comment>(`/students/${studentId}/comments`, { body }).then((r) => r.data);

// --- finance (teacher) ---
export const financeSummary = () =>
  api.get<FinanceSummary>("/finance/summary").then((r) => r.data);
export const dashboardStats = () =>
  api.get<DashboardStats>("/dashboard/stats").then((r) => r.data);
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
export const markHomework = (id: number, data: { is_done?: boolean; student_answer?: string }) =>
  api.patch<Homework>(`/me/homeworks/${id}`, data).then((r) => r.data);
export const myComments = () => api.get<Comment[]>("/me/comments").then((r) => r.data);
export const addMyComment = (body: string) =>
  api.post<Comment>("/me/comments", { body }).then((r) => r.data);

// --- parent ---
export const fetchChildren = () =>
  api.get<ParentOverview>("/parent/children").then((r) => r.data);
export const fetchChild = (studentId: number) =>
  api.get<ChildCard>(`/parent/child/${studentId}`).then((r) => r.data);
export const fetchBalance = (studentId: number) =>
  api.get<Balance>(`/parent/balance/${studentId}`).then((r) => r.data);
// учитель: список родителей для привязки второго ребёнка
export const listTeacherParents = () =>
  api.get<TeacherParent[]>("/teacher/parents").then((r) => r.data);
export const attachParent = (
  studentId: number,
  data: { parent_user_id: number; lesson_price: string; recommendations?: string },
) => api.post<Parent>(`/students/${studentId}/parents/attach`, data).then((r) => r.data);
