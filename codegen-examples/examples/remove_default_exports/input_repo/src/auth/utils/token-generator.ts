// Original file keeps default export
export default function generateToken(): string {
	return Math.random().toString(36);
}
