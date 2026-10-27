import { beforeEach, describe, expect, it, vi } from 'vitest';
import { mount } from '@vue/test-utils';
import axios from 'axios';
import Post from '@/views/Post.vue';

const push = vi.fn();

vi.mock('@/router', () => ({
  useRouter: () => ({
    push,
    currentRoute: { value: { params: {}, query: {} } },
  }),
}));

vi.mock('@/store', () => ({
  useStore: () => ({
    getters: { getToken: 'dummy-token' },
  }),
}));

vi.mock('axios', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    patch: vi.fn(),
    delete: vi.fn(),
  },
}));

const mockedAxios = axios as unknown as {
  post: ReturnType<typeof vi.fn>;
};

describe('Post.vue', () => {
  beforeEach(() => {
    push.mockClear();
    mockedAxios.post.mockReset();
  });

  it('句を入力して投函すると、公開句として送信され詳細画面に遷移する(正常系)', async () => {
    mockedAxios.post.mockResolvedValue({ data: { id: 123 } });
    const wrapper = mount(Post);

    const textarea = wrapper.find('textarea');
    await textarea.setValue('古池や蛙飛び込む水の音');
    await wrapper.find('.post-button').trigger('click');
    await flushPromisesOnce();

    expect(mockedAxios.post).toHaveBeenCalledWith(
      '/api/haikus/',
      { content: '古池や蛙飛び込む水の音', isPublic: true },
      expect.objectContaining({
        headers: expect.objectContaining({ Authorization: 'JWT dummy-token' }),
      }),
    );
    expect(push).toHaveBeenCalledWith('/detail/123');
  });

  it('非公開にするチェックを入れると isPublic:false で送信される(正常系)', async () => {
    mockedAxios.post.mockResolvedValue({ data: { id: 124 } });
    const wrapper = mount(Post);

    await wrapper.find('textarea').setValue('非公開の句');
    await wrapper.find('.visibility-checkbox').setValue(true);
    await wrapper.find('.post-button').trigger('click');
    await flushPromisesOnce();

    expect(mockedAxios.post).toHaveBeenCalledWith(
      '/api/haikus/',
      { content: '非公開の句', isPublic: false },
      expect.anything(),
    );
  });

  it('空の句の場合、投函ボタンは無効化され送信されない(異常系)', async () => {
    const wrapper = mount(Post);

    const button = wrapper.find('.post-button');
    expect(button.attributes('disabled')).toBeDefined();

    await button.trigger('click');

    expect(mockedAxios.post).not.toHaveBeenCalled();
  });

  it('51文字目以降の入力は切り詰められる(異常系/境界値)', async () => {
    const wrapper = mount(Post);
    const longText = 'あ'.repeat(60);

    await wrapper.find('textarea').setValue(longText);

    expect(wrapper.find('.char-count').text()).toBe('50 / 50');
  });
});

function flushPromisesOnce(): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, 0));
}
