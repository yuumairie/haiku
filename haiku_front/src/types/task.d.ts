export interface UserModel {
  id: number;
  username: string;
  avatar?: string | null;
}

export interface HaikuModel {
  id: number;
  userPost: {
    id: number;
    username: string;
    avatar?: string | null;
  };
  content?: string;
  createdAt?: string;
  good?: Array<UserModel>;
  kigo?: string | null;
  season?: string | null;
  isPublic?: boolean;
}

export interface GoodModel {
  id: number;
  user: string;
  haiku: string;
}

export interface CommentModel {
  id: number;
  text: string;
  userComment: {
    id: number;
    username: string;
  };
  post: number;
}

export interface FollowModel {
  id: number;
  follower: UserModel;
  following: UserModel;
}
