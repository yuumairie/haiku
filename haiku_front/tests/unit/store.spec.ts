import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import axios from 'axios';
import { MutationTypes, store } from '@/store';

// store/index.tsはモジュールレベルでシングルトンのstoreを作っているため、
// このファイル内の各テストの前にLOGOUTでリセットして影響を残さないようにする。
vi.mock('axios', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    patch: vi.fn(),
    delete: vi.fn(),
    interceptors: {
      request: { use: vi.fn() },
      response: { use: vi.fn() },
    },
  },
}));

const mockedAxios = axios as unknown as {
  get: ReturnType<typeof vi.fn>;
  post: ReturnType<typeof vi.fn>;
};

const flushPromises = (): Promise<void> => new Promise((resolve) => setTimeout(resolve, 0));

describe('store mutations', () => {
  beforeEach(() => {
    store.commit(MutationTypes.LOGOUT);
    localStorage.clear();
    vi.clearAllMocks();
  });

  afterEach(() => {
    store.commit(MutationTypes.LOGOUT);
  });

  it('LOGOUTはjwt・userId・name・email・goodList・followList・homeTabを初期値に戻す(正常系)', () => {
    store.commit(MutationTypes.GOOD, [{ id: 1, user: 'u', haiku: 'h' }] as never);
    store.commit(MutationTypes.SET_HOME_TAB, 'liked');

    store.commit(MutationTypes.LOGOUT);

    expect(store.getters.getToken).toBe('');
    expect(store.getters.getUserId).toBe(0);
    expect(store.getters.getGoodList).toEqual([]);
    expect(store.getters.getFollowList).toEqual([]);
    expect(store.getters.getHomeTab).toBe('new');
  });

  it('GOODはgoodListをそのまま置き換える(正常系)', () => {
    const payload = [{ id: 1, user: '1', haiku: '2' }];
    store.commit(MutationTypes.GOOD, payload as never);
    expect(store.getters.getGoodList).toEqual(payload);
  });

  it('FOLLOW_LISTはfollowListをそのまま置き換える(正常系)', () => {
    const payload = [{ id: 1, follower: {}, following: {} }];
    store.commit(MutationTypes.FOLLOW_LIST, payload as never);
    expect(store.getters.getFollowList).toEqual(payload);
  });

  it('SET_HOME_TABはhomeTabを更新する(正常系)', () => {
    store.commit(MutationTypes.SET_HOME_TAB, 'following');
    expect(store.getters.getHomeTab).toBe('following');
  });

  it('LOGINはトークンを保存し、プロフィール取得に成功するとuserIdとfollowListを設定する(正常系)', async () => {
    mockedAxios.get.mockImplementation((url: string) => {
      if (url === '/api/myprofile/') {
        return Promise.resolve({ data: [{ id: 42 }] });
      }
      if (url === '/api/follows/') {
        return Promise.resolve({ data: [{ id: 1, follower: {}, following: {} }] });
      }
      return Promise.reject(new Error(`unexpected url: ${url}`));
    });

    store.commit(MutationTypes.LOGIN, 'valid-token');
    await flushPromises();
    await flushPromises();

    expect(store.getters.getToken).toBe('valid-token');
    expect(store.getters.getUserId).toBe(42);
    expect(store.getters.getFollowList).toHaveLength(1);
    expect(localStorage.getItem('haiku_jwt')).toBe('valid-token');
  });

  it('LOGINはプロフィール取得に失敗するとトークンをクリアする(異常系)', async () => {
    mockedAxios.get.mockRejectedValue(new Error('invalid token'));

    store.commit(MutationTypes.LOGIN, 'invalid-token');
    await flushPromises();
    await flushPromises();

    expect(store.getters.getToken).toBe('');
    expect(store.getters.getUserId).toBe(0);
    expect(localStorage.getItem('haiku_jwt')).toBeNull();
  });
});
