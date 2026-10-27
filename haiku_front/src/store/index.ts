import {
  createStore,
  MutationTree,
  ActionContext,
  ActionTree,
  GetterTree,
  Store as VuexStore,
  CommitOptions,
  DispatchOptions,
  createLogger,
} from 'vuex';
import axios from 'axios';
import { GoodModel, FollowModel } from '../types/task.d';

// リロードしてもログイン状態を保持するためのlocalStorageキー
const JWT_STORAGE_KEY = 'haiku_jwt';

const loadStoredToken = (): string => {
  try {
    return localStorage.getItem(JWT_STORAGE_KEY) || '';
  } catch (e) {
    console.error(e);
    return '';
  }
};

const persistToken = (token: string): void => {
  try {
    localStorage.setItem(JWT_STORAGE_KEY, token);
  } catch (e) {
    console.error(e);
  }
};

const clearStoredToken = (): void => {
  try {
    localStorage.removeItem(JWT_STORAGE_KEY);
  } catch (e) {
    console.error(e);
  }
};

// ホーム画面（皆の句）で選択中のタブ。戻るボタンで画面に戻った時にも
// 選択していたタブを復元できるよう、コンポーネントのローカル状態ではなく
// ストアで持つ
export type HomeTab = 'new' | 'following' | 'liked';

export type State = {
  name: string;
  email: string;
  jwt: string;
  userId: number;
  goodList: Array<GoodModel>;
  followList: Array<FollowModel>;
  homeTab: HomeTab;
};
const state: State = {
  name: '',
  email: '',
  // 起動時にlocalStorageに保存済みのJWTがあれば復元する
  jwt: loadStoredToken(),
  userId: 0,
  goodList: [],
  followList: [],
  homeTab: 'new',
};

export enum MutationTypes {
  LOGIN = 'LOGIN',
  LOGOUT = 'LOGOUT',
  GOOD = 'GOOD',
  FOLLOW_LIST = 'FOLLOW_LIST',
  SET_HOME_TAB = 'SET_HOME_TAB',
}
export enum ActionTypes {
  LOGIN = 'LOGIN',
  GOOD = 'GOOD',
  FOLLOW_LIST = 'FOLLOW_LIST',
}

export type Mutations<S = State> = {
  [MutationTypes.LOGIN](state: S, payload: string): void;
  [MutationTypes.LOGOUT](state: S): void;
  [MutationTypes.GOOD](state: S, payload: Array<GoodModel>): void;
  [MutationTypes.FOLLOW_LIST](state: S, payload: Array<FollowModel>): void;
  [MutationTypes.SET_HOME_TAB](state: S, payload: HomeTab): void;
};

const mutations: MutationTree<State> & Mutations = {
  // login mutation（画面ロード時の復元でも使う）
  [MutationTypes.LOGIN](state: State, payload: string) {
    state.jwt = payload;
    persistToken(payload);
    const headers = {
      'Content-Type': 'application/json',
      Authorization: `JWT ${payload}`,
    };
    axios
      .get('/api/myprofile/', {
        headers: headers,
      })
      .then((res) => {
        state.userId = res.data[0].id;
        // 自分がフォローしているユーザ一覧を取得する（userId確定後に行う）
        axios
          .get('/api/follows/', {
            headers: headers,
            params: { follower: state.userId },
          })
          .then((followRes) => {
            state.followList = followRes.data;
          })
          .catch((followErr) => {
            console.error(followErr);
          });
      })
      .catch((err) => {
        console.error(err);
        // トークンが無効・期限切れの場合はログイン状態をクリアする
        state.jwt = '';
        state.userId = 0;
        clearStoredToken();
      });
  },

  // logout mutation
  [MutationTypes.LOGOUT](state: State) {
    state.jwt = '';
    state.userId = 0;
    state.name = '';
    state.email = '';
    state.goodList = [];
    state.followList = [];
    // 購読中・いいねタブはログイン前提のため、ログアウト時は新着に戻す
    state.homeTab = 'new';
    clearStoredToken();
  },

  // good mutation
  [MutationTypes.GOOD](state: State, payload: Array<GoodModel>) {
    state.goodList = payload;
  },

  // follow list mutation
  [MutationTypes.FOLLOW_LIST](state: State, payload: Array<FollowModel>) {
    state.followList = payload;
  },

  // ホーム画面のタブ選択状態を保持するmutation
  [MutationTypes.SET_HOME_TAB](state: State, payload: HomeTab) {
    state.homeTab = payload;
  },
};

type AugmentedActionContext = {
  commit<k extends keyof Mutations>(
    key: k,
    payload: Parameters<Mutations[k]>[1],
  ): ReturnType<Mutations[k]>;
} & Omit<ActionContext<State, State>, 'commit'>;

export interface Actions {
  [ActionTypes.LOGIN](
    { commit }: AugmentedActionContext,
    payload: {
      email: string;
      password: string;
    },
  ): void;

  [ActionTypes.GOOD]({ commit }: AugmentedActionContext): void;

  [ActionTypes.FOLLOW_LIST]({ commit }: AugmentedActionContext): void;
}

export const actions: ActionTree<State, State> & Actions = {
  // login action
  [ActionTypes.LOGIN]({ commit }, data) {
    return new Promise((resolve, reject) => {
      axios
        .post('/authen/jwt/create', data)
        .then((res) => {
          commit(MutationTypes.LOGIN, res.data.access);
          resolve(res.data.access);
        })
        .catch((err) => {
          reject(err);
        });
    });
  },

  // good action
  [ActionTypes.GOOD]({ commit }) {
    const headers = {
      'Content-Type': 'application/json',
      Authorization: `JWT ${state.jwt}`,
    };
    axios
      .get('/api/goods/', {
        headers: headers,
      })
      .then((res) => {
        commit(MutationTypes.GOOD, res.data);
      })
      .catch((err) => {
        console.error(err);
      });
  },

  // follow list action（フォロー・フォロー解除のたびに最新化する）
  [ActionTypes.FOLLOW_LIST]({ commit }) {
    const headers = {
      'Content-Type': 'application/json',
      Authorization: `JWT ${state.jwt}`,
    };
    axios
      .get('/api/follows/', {
        headers: headers,
        params: { follower: state.userId },
      })
      .then((res) => {
        commit(MutationTypes.FOLLOW_LIST, res.data);
      })
      .catch((err) => {
        console.error(err);
      });
  },
};
export type Getters = {
  getToken(state: State): string;
  getUserId(state: State): number;
  getGoodList(state: State): Array<GoodModel>;
  getFollowList(state: State): Array<FollowModel>;
  getHomeTab(state: State): HomeTab;
};

export const getters: GetterTree<State, State> & Getters = {
  getToken: (state) => {
    return state.jwt;
  },
  getUserId: (state) => {
    return state.userId;
  },
  getGoodList: (state) => {
    return state.goodList;
  },
  getFollowList: (state) => {
    return state.followList;
  },
  getHomeTab: (state) => {
    return state.homeTab;
  },
};

export type Store = Omit<VuexStore<State>, 'commit' | 'getters' | 'dispatch'> & {
  commit<k extends keyof Mutations, P extends Parameters<Mutations[k]>[1]>(
    key: k,
    payload: P,
    options?: CommitOptions,
  ): ReturnType<Mutations[k]>;
} & {
  getters: {
    [K in keyof Getters]: ReturnType<Getters[K]>;
  };
} & {
  dipatch<K extends keyof Actions>(
    key: K,
    payload: Parameters<Actions[K]>[1],
    options?: DispatchOptions,
  ): ReturnType<Actions[K]>;
};

export const store = createStore({
  state,
  mutations,
  actions,
  getters,
  plugins: [createLogger()],
});

export const useStore = () => {
  return store;
};
