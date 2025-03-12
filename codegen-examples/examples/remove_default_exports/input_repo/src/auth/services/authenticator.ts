// Original file keeps default export
export default class Authenticator {
	authenticate(token: string): boolean {
		return token.length > 0;
	}
}
