export function getUser(): { name: string; age: number } {
  return { name: "John Doe", age: 30 };
}

function formatUserName(firstName: string, lastName: string): string {
  return `${firstName} ${lastName}`;
}
