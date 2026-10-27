import { describe, expect, it, vi } from 'vitest';
import { mount } from '@vue/test-utils';
import HaikuCard from '@/components/HaikuCard.vue';

// HaikuCard.vueのテンプレートはisNotLoginUser=trueの分岐でのみ
// require('@/assets/images/...')を呼ぶ。Vitestのビルド環境でこのrequire呼び出し
// を解決できるかはテスト対象外のため、常にisNotLoginUser=falseでマウントして
// この分岐を避ける。
vi.mock('@/router', () => ({
  useRouter: () => ({
    push: vi.fn(),
    currentRoute: { value: { fullPath: '/home' } },
  }),
}));

vi.mock('@/store', () => ({
  ActionTypes: { GOOD: 'GOOD' },
  useStore: () => ({
    getters: {
      getUserId: 1,
      getGoodList: [],
      getToken: 'dummy-token',
    },
    dispatch: vi.fn(),
  }),
}));

const baseHaiku = {
  id: 10,
  content: '古池や蛙飛び込む水の音',
  createdAt: '2026/01/01 10:00',
  good: [],
  kigo: null,
  season: null,
  isPublic: true,
  userPost: { id: 2, username: 'ばしょう', avatar: null },
};

describe('HaikuCard', () => {
  it('公開中の句には非公開バッジを表示しない(正常系)', () => {
    const wrapper = mount(HaikuCard, {
      props: { haiku: baseHaiku, isNotLoginUser: false },
    });

    expect(wrapper.find('.private-badge').exists()).toBe(false);
    expect(wrapper.text()).toContain('古池や蛙飛び込む水の音');
    expect(wrapper.text()).toContain('ばしょう');
  });

  it('非公開の句には「非公開」バッジを表示する(異常系/境界値)', () => {
    const wrapper = mount(HaikuCard, {
      props: { haiku: { ...baseHaiku, isPublic: false }, isNotLoginUser: false },
    });

    expect(wrapper.find('.private-badge').exists()).toBe(true);
    expect(wrapper.find('.private-badge').text()).toBe('非公開');
  });

  it('投稿者の表示名が無い場合は「匿名」と表示する(異常系/境界値)', () => {
    const wrapper = mount(HaikuCard, {
      props: {
        haiku: { ...baseHaiku, userPost: { id: 3, username: '', avatar: null } },
        isNotLoginUser: false,
      },
    });

    expect(wrapper.text()).toContain('匿名');
  });

  it('ゆかし(いいね)の件数をgood配列の長さで表示する(正常系)', () => {
    const wrapper = mount(HaikuCard, {
      props: {
        haiku: { ...baseHaiku, good: [{ id: 1 }, { id: 2 }] },
        isNotLoginUser: false,
      },
    });

    expect(wrapper.find('.count').text()).toBe('2');
  });
});
