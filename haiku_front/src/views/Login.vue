<template>
  <div class="login-page">
    <label style="font-size: 24px; background: linear-gradient(transparent 50%, #a8eaff 50%)">
      ログイン
    </label>
    <br /><br />
    <div class="info">
      <div class="email">
        <label for="address">アドレス</label>
        <br />
        <input type="email" id="address" v-model="state.email" />
      </div>
      <br />
      <div class="password">
        <label for="password">パスワード</label>
        <br />
        <input type="password" id="password" v-model="state.password" />
      </div>
      <br />
      <div class="error-message" v-for="errorMessage in state.errorMessageList" :key="errorMessage">
        {{ errorMessage }}
      </div>
      <br />
      <div>
        <button @click="login()">ログイン</button>
      </div>
      <br />
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent, reactive } from 'vue';
import { useStore, ActionTypes } from '../store';
import { useRouter } from '../router';

const fieldLabels: Record<string, string> = {
  email: 'アドレス',
  username: 'ユーザ名',
  password: 'パスワード',
};

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
      errorMessageList: [] as string[],
    });
    const store = useStore();
    const router = useRouter();

    const validate = () => {
      if (!state.email) {
        state.errorMessageList.push('アドレスの入力は必須です');
      }
      if (!state.password) {
        state.errorMessageList.push('パスワードの入力は必須です');
      }
      return state.errorMessageList.length ? true : false;
    };

    //ログイン
    const login = () => {
      state.errorMessageList = [];
      if (validate()) {
        return;
      }
      const data = {
        email: state.email,
        password: state.password,
      };

      //jwt取得
      store
        .dispatch(ActionTypes.LOGIN, data)
        .then((resp) => {
          //ユーザのいいね一覧取得
          store.dispatch(ActionTypes.GOOD);
          //ホーム画面へ移動
          router.push('home');
        })
        .catch((err) => {
          state.errorMessageList.push(buildErrorMessage(err));
        });
    };
    return { state, login };
  },
});
</script>

<style scoped>
.login-page {
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
.info {
  border: black 2px dashed;
  width: 400px;
  margin: auto;
}
</style>
