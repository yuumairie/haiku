import { beforeEach, describe, expect, it, vi } from 'vitest';
import { flushPromises, mount } from '@vue/test-utils';
import axios from 'axios';
import Edit from '@/views/Edit.vue';

const push = vi.fn();

vi.mock('@/router', () => ({
  useRouter: () => ({
    push,
    currentRoute: { value: { params: { id: '7' }, query: { from: 'mine' } } },
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
  get: ReturnType<typeof vi.fn>;
  patch: ReturnType<typeof vi.fn>;
};

describe('Edit.vue', () => {
  beforeEach(() => {
    push.mockClear();
    mockedAxios.get.mockReset();
    mockedAxios.patch.mockReset();
  });

  it('マウント時に既存の句を取得し、フォームに反映する(正常系)', async () => {
    mockedAxios.get.mockResolvedValue({
      data: { content: '元の句', kigo: '桜', season: '春', isPublic: false },
    });

    const wrapper = mount(Edit);
    await flushPromises();

    expect(mockedAxios.get).toHaveBeenCalledWith('api/haikus/7/');
    expect((wrapper.find('textarea').element as HTMLTextAreaElement).value).toBe('元の句');
    expect((wrapper.find('#kigo').element as HTMLInputElement).value).toBe('桜');
    expect((wrapper.find('.visibility-checkbox').element as HTMLInputElement).checked).toBe(true);
  });

  it('更新に成功すると詳細画面に戻る(正常系)', async () => {
    mockedAxios.get.mockResolvedValue({
      data: { content: '元の句', kigo: '', season: '', isPublic: true },
    });
    mockedAxios.patch.mockResolvedValue({});

    const wrapper = mount(Edit);
    await flushPromises();

    await wrapper.find('textarea').setValue('直した句');
    await wrapper.find('.post-button').trigger('click');
    await flushPromises();

    expect(mockedAxios.patch).toHaveBeenCalledWith(
      'api/haikus/7/',
      expect.objectContaining({ content: '直した句', isPublic: true }),
      expect.anything(),
    );
    expect(push).toHaveBeenCalledWith({ path: '/detail/7', query: { from: 'mine' } });
  });

  it('季語が本文に含まれていないサーバーエラーの場合、エラーメッセージを表示する(異常系)', async () => {
    mockedAxios.get.mockResolvedValue({
      data: { content: '元の句', kigo: '', season: '', isPublic: true },
    });
    mockedAxios.patch.mockRejectedValue({
      response: { data: { kigo: ['入力した季語が俳句の本文に含まれていません。'] } },
    });

    const wrapper = mount(Edit);
    await flushPromises();

    await wrapper.find('#kigo').setValue('桜');
    await wrapper.find('.post-button').trigger('click');
    await flushPromises();

    expect(wrapper.find('.kigo-error').text()).toBe('入力した季語が俳句の本文に含まれていません。');
    expect(push).not.toHaveBeenCalled();
  });

  it('空の句の場合、更新ボタンは無効化される(異常系)', async () => {
    mockedAxios.get.mockResolvedValue({
      data: { content: '', kigo: '', season: '', isPublic: true },
    });

    const wrapper = mount(Edit);
    await flushPromises();

    expect(wrapper.find('.post-button').attributes('disabled')).toBeDefined();
  });
});
