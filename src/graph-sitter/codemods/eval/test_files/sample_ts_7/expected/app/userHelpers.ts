export function getUser() {
  return { name: "John Doe", age: 30 };
}

/* @internal */
function formatUserName(firstName, lastName) {
  return `${firstName} ${lastName}`;
}
