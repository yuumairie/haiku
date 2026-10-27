import { createApp } from 'vue';
import App from './App.vue';
import { router } from './router';
import { store, MutationTypes, ActionTypes } from './store';
import axios from 'axios';

axios.defaults.baseURL = process.env.VUE_APP_API_BASE_URL || 'http://localhost:8000';

// リロード時にlocalStorageへ保存済みのJWTがあればログイン状態を復元する
// （LOGINミューテーションがプロフィール取得も行い、トークンが無効なら
//  自動的にログアウト状態に戻す）
if (store.state.jwt) {
  store.commit(MutationTypes.LOGIN, store.state.jwt);
  store.dispatch(ActionTypes.GOOD);
}

createApp(App).use(store).use(router).mount('#app');
