import { UserRole } from "./enums";
export interface User {
  id: string;
  name: string;
  role: UserRole;
}
