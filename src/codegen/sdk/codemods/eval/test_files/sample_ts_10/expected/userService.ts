import { User, UserRole } from "./types";

enum UserStatus {
  ACTIVE = "active",
  INACTIVE = "inactive",
}

interface UserDetails {
  email: string;
  status: UserStatus;
}

async function fetchUser(id: string): Promise<User> {
  return new Promise((resolve, reject) => {
    setTimeout(() => {
      if (id === "1") {
        resolve({ id: "1", name: "John Doe", role: UserRole.ADMIN });
      } else {
        reject(new Error("User not found"));
      }
    }, 1000);
  });
}

async function getUserDetails(user: User): Promise<UserDetails> {
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve({
        email: `${user.name.toLowerCase()}@example.com`,
        status: UserStatus.ACTIVE,
      });
    }, 500);
  });
}

export async function getFullUserInfo(id: string): Promise<User & UserDetails> {
  try {
    const user = await fetchUser(id);
    const details = await getUserDetails(user);
    return { ...user, ...details };
  } catch (error) {
    console.error("Error fetching user:", error);
    throw error;
  }
}
