export const calculateSum = (a: number, b: number): number => {
	return a + b;
};

export const formatName = (firstName: string, lastName: string): string => {
	return `${firstName} ${lastName}`;
};

export const generateId = (): string => {
	return Math.random().toString(36).substring(7);
};

export const validateEmail = (email: string): boolean => {
	const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
	return emailRegex.test(email);
};

export const capitalize = (str: string): string => {
	return str.charAt(0).toUpperCase() + str.slice(1).toLowerCase();
};
