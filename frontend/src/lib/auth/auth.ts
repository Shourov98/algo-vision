import { apiFetch } from "@/lib/api/client";

export interface CurrentUser {
  id: string;
  email: string;
  display_name?: string;
  role?: string;
}

interface CurrentUserResponse {
  data?: CurrentUser;
}

export async function getCurrentUser(): Promise<CurrentUser> {
  const response = await apiFetch<CurrentUser | CurrentUserResponse>("auth/me");
  return "data" in response && response.data ? response.data : (response as CurrentUser);
}
