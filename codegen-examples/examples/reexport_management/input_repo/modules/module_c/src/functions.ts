import {
	calculateAverage,
	createUserProfile,
	generateId,
	multiply,
	validateEmail,
} from "./shared/symbols/exports";

export const createUser = (
	email: string,
	firstName: string,
	lastName: string,
) => {
	if (!validateEmail(email)) {
		throw new Error("Invalid email");
	}

	return {
		id: generateId(),
		profile: createUserProfile(firstName, lastName),
		email,
	};
};

export const calculateMetrics = (
	values: number[],
): { average: number; scaled: number[] } => {
	const avg = calculateAverage(values);
	const scaled = values.map((v) => multiply(v, 2));
	return { average: avg, scaled };
};

export const validateAndFormatUser = (
	email: string,
	firstName: string,
	lastName: string,
) => {
	if (!validateEmail(email)) {
		return { success: false, message: "Invalid email" };
	}

	const profile = createUserProfile(firstName, lastName);
	return { success: true, profile };
};

export const processNumbers = (numbers: number[]): number => {
	const { average } = calculateMetrics(numbers);
	return multiply(average, 100);
};

export const generateReport = (userData: {
	email: string;
	name: string;
}): string => {
	const isValidEmail = validateEmail(userData.email);
	const id = generateId();
	return `Report ${id}: Email ${isValidEmail ? "valid" : "invalid"} - ${userData.name}`;
};
