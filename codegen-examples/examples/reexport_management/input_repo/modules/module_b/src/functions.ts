import {
	calculateSum,
	capitalize,
	formatName,
	validateEmail,
} from "./shared/exports";

export const calculateAverage = (numbers: number[]): number => {
	const sum = numbers.reduce((acc, curr) => calculateSum(acc, curr), 0);
	return sum / numbers.length;
};

export const createUserProfile = (
	firstName: string,
	lastName: string,
): string => {
	const formattedName = formatName(firstName, lastName);
	return `Profile: ${formattedName}`;
};

export const formatText = (text: string): string => {
	return text.split(" ").map(capitalize).join(" ");
};

export const multiply = (a: number, b: number): number => {
	return a * b;
};

export const generateGreeting = (name: string): string => {
	const email = validateEmail(name);
	return `Hello, ${capitalize(name)}!`;
};
