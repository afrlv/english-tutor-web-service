import axios from "axios";

export const api = axios.create({
  baseURL: "/api",
  withCredentials: true,
});

// 401 → сброс сессии и редирект на логин (настраивается в router/index.ts,
// чтобы избежать циклического импорта)
export function onUnauthorized(handler: () => void) {
  api.interceptors.response.use(undefined, (error) => {
    if (error.response?.status === 401) handler();
    return Promise.reject(error);
  });
}
