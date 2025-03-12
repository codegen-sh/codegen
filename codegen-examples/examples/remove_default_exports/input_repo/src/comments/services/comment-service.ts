// Original file keeps default export
import type Comment from "../models/comment";

export default class CommentService {
	getComment(id: string): Comment {
		return { id, postId: "123", text: "Great post!" };
	}
}
