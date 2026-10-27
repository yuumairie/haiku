import { createApp } from 'vue';
import App from './App.vue';
import { router } from './router';
import { store, MutationTypes, ActionTypes } from './store';
import axios from 'axios';
import { toCamelCase, toSnakeCase } from './utils/caseConverter';

axios.defaults.baseURL = process.env.VUE_APP_API_BASE_URL || 'http://localhost:8000';

// フロント側はcamelCaseに統一する。バックエンド(snake_case)との変換は
// ここで一括して行うので、各画面のコードではsnake_caseを書かなくてよい。
// アバター画像のアップロードで使うFormDataはキー変換の対象外にする。
axios.interceptors.request.use((config) => {
  if (config.data && !(config.data instanceof FormData)) {
    config.data = toSnakeCase(config.data);
  }
  if (config.params) {
    config.params = toSnakeCase(config.params);
  }
  return config;
});

axios.interceptors.response.use(
  (response) => {
    response.data = toCamelCase(response.data);
    return response;
  },
  (error) => {
    if (error.response && error.response.data) {
      error.response.data = toCamelCase(error.response.data);
    }
    return Promise.reject(error);
  }
);

// リロード時にlocalStorageへ保存済みのJWTがあればログイン状態を復元する
// （LOGINミューテーションがプロフィール取得も行い、トークンが無効なら
//  自動的にログアウト状態に戻す）
if (store.state.jwt) {
  store.commit(MutationTypes.LOGIN, store.state.jwt);
  store.dispatch(ActionTypes.GOOD);
}

createApp(App).use(store).use(router).mount('#app');
