<template>
  <div class="register-page">
    <label style="font-size: 24px; background: linear-gradient(transparent 50%, #a8eaff 50%)">
      アカウント情報を入力
    </label>
    <br />
    <br />
    <div class="info">
      <div>
        <label for="name">ユーザ名</label>
        <br />
        <input type="text" id="name" v-model="state.name" required />
      </div>
      <br />
      <div>
        <label for="address">アドレス</label>
        <br />
        <input type="email" id="address" v-model="state.email" />
      </div>
      <br />
      <div>
        <label for="password">パスワード</label>
        <br />
        <input type="password" id="password" v-model="state.password" />
      </div>
      <br />
      <div v-if="state.errorMessage" class="error-message">
        {{ state.errorMessage }}
      </div>
      <br v-if="state.errorMessage" />
      <div>
        <button @click="create()" :disabled="state.loading">アカウント作成</button>
      </div>
      <br />
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent, reactive } from 'vue';
import { useStore, ActionTypes } from '../store';
import { useRouter } from '../router';
import axios from 'axios';

// APIのフィールド名 -> 画面表示用ラベル
const fieldLabels: Record<string, string> = {
  email: 'アドレス',
  username: 'ユーザ名',
  password: 'パスワード',
};

// axiosのエラーからユーザに見せる文言を組み立てる
const buildErrorMessage = (err: any): string => {
  const response = err?.response;

  // サーバーには届いたがバリデーションエラー等が返ってきた場合
  if (response?.data && typeof response.data === 'object') {
    const lines: string[] = [];
    Object.keys(response.data).forEach((key) => {
      const label = fieldLabels[key] ?? key;
      const value = response.data[key];
      const texts = Array.isArray(value) ? value : [value];
      texts.forEach((text) => {
        lines.push(label ? `${label}: ${text}` : String(text));
      });
    });
    if (lines.length > 0) {
      return lines.join('\n');
    }
  }

  // サーバーには届いたがハンドリングできない形式のエラー
  if (response) {
    return `登録に失敗しました。(エラーコード: ${response.status})`;
  }

  // サーバーに届かなかった場合（通信エラー・サーバー停止など）
  return 'サーバーに接続できませんでした。しばらくしてから再度お試しください。';
};

export default defineComponent({
  setup() {
    const state = reactive({
      name: '',
      email: '',
      password: '',
      loading: false,
      errorMessage: '',
    });
    const store = useStore();
    const router = useRouter();

    //アカウント作成関数
    const create = () => {
      state.errorMessage = '';

      //ユーザ名が未入力だと一覧画面で「匿名」表示になってしまうため、
      //送信前にチェックする
      if (!state.name.trim()) {
        state.errorMessage = 'ユーザ名: この項目は必須です。';
        return;
      }

      state.loading = true;
      const data = {
        email: state.email,
        password: state.password,
        username: state.name,
      };
      //アカウント作成
      axios
        .post('/api/register/', data)
        .then(() => {
          //jwt取得
          store
            .dispatch(ActionTypes.LOGIN, data)
            .then(() => {
              //ホーム画面へ移動
              router.push('home');
            })
            .catch(() => {
              // 登録自体は成功しているので、その旨を伝える
              state.errorMessage =
                'アカウントは作成されましたが、ログインに失敗しました。ログイン画面から再度ログインしてください。';
            })
            .finally(() => {
              state.loading = false;
            });
        })
        .catch((err) => {
          state.errorMessage = buildErrorMessage(err);
          state.loading = false;
        });
    };
    return { state, create };
  },
});
</script>

<style scoped>
.register-page .info {
  border: black 2px dashed;
  width: 400px;
  margin: auto;
}
.register-page {
  text-align: center;
}
input {
  height: 1.5em;
  width: 17em;
}
.error-message {
  color: #d32f2f;
  background: #fdecea;
  border: 1px solid #d32f2f;
  border-radius: 4px;
  padding: 8px 12px;
  margin: 8px auto 0;
  width: 360px;
  white-space: pre-line;
  text-align: left;
  font-size: 14px;
}
</style>
