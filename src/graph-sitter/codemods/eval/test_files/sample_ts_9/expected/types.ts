export enum UserRole {
  ADMIN = "admin",
  USER = "user",
  GUEST = "guest",
}

export interface User {
  readonly id: string;
  readonly name: string;
  readonly role: UserRole;
}
