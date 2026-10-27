<template>
  <div class="profile-page">
    <h2 class="profile-title">プロフィール</h2>

    <div class="profile-card">
      <div class="avatar-area">
        <div class="avatar-preview">
          <img v-if="state.avatarPreview" :src="state.avatarPreview" class="avatar-img" />
          <div v-else class="avatar-placeholder">{{ initial }}</div>
        </div>
        <label class="avatar-upload">
          画像を選択
          <input type="file" accept="image/*" class="avatar-input" @change="onAvatarChange" />
        </label>
        <div class="avatar-hint">{{ MAX_AVATAR_SIZE_MB }}MB以下の画像を選択してください</div>
      </div>

      <div class="field-row">
        <label class="field-label" for="username">表示名</label>
        <input
          id="username"
          v-model="state.username"
          type="text"
          class="field-input"
          placeholder="ユーザー名"
          maxlength="20"
        />
      </div>

      <div v-if="state.errorMessage" class="form-message error">{{ state.errorMessage }}</div>
      <div v-if="state.successMessage" class="form-message success">
        {{ state.successMessage }}
      </div>

      <div class="actions">
        <button class="save-button" :disabled="state.saving || !state.username.trim()" @click="save()">
          {{ state.saving ? '保存中…' : '保存する' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent, onMounted, reactive, computed } from 'vue';
import axios from 'axios';
import { useStore } from '../store';

// バックエンド（Profile.imgのvalidate_avatar_size）と同じ上限に揃える
const MAX_AVATAR_SIZE_MB = 5;
const MAX_AVATAR_SIZE_BYTES = MAX_AVATAR_SIZE_MB * 1024 * 1024;

export default defineComponent({
  name: 'my-profile',
  setup() {
    const store = useStore();

    const state = reactive({
      username: '',
      avatarFile: null as File | null,
      avatarPreview: '',
      profileId: 0,
      saving: false,
      errorMessage: '',
      successMessage: '',
    });

    const jwt = computed(() => {
      return store.getters.getToken;
    });

    const authHeaders = () => ({
      Authorization: `JWT ${jwt.value}`,
    });

    //表示名が未取得の間、アバター未設定時のプレースホルダに表示する頭文字
    const initial = computed(() => {
      return state.username ? state.username.charAt(0) : '?';
    });

    //ログイン中の自分自身の表示名（username）を取得する
    const getMe = (): void => {
      axios
        .get('/api/me/', { headers: authHeaders() })
        .then((req) => {
          state.username = req.data.username || '';
        })
        .catch((err) => {
          console.error(err);
        });
    };

    //自分のプロフィール（画像など）を取得する。まだ作成していない場合は何も無い
    const getProfile = (): void => {
      axios
        .get('/api/profiles/', {
          params: { userProfile: store.getters.getUserId },
        })
        .then((req) => {
          if (req.data.length) {
            state.profileId = req.data[0].id;
            state.avatarPreview = req.data[0].img || '';
          }
        })
        .catch((err) => {
          console.error(err);
        });
    };

    onMounted(() => {
      getMe();
      getProfile();
    });

    //画像選択時、すぐに見た目へ反映する（保存前のプレビュー）。
    //大きすぎる画像はサーバーに送る前にここで弾く（サーバー側にも同じ上限の
    //バリデーションがあるが、選択直後にすぐ分かるようにする）
    const onAvatarChange = (event: Event): void => {
      const input = event.target as HTMLInputElement;
      const file = input.files && input.files[0];
      input.value = '';
      if (!file) {
        return;
      }
      if (file.size > MAX_AVATAR_SIZE_BYTES) {
        state.errorMessage = `画像サイズは${MAX_AVATAR_SIZE_MB}MB以下にしてください。`;
        return;
      }
      state.errorMessage = '';
      state.avatarFile = file;
      state.avatarPreview = URL.createObjectURL(file);
    };

    //表示名（username）を更新する
    const saveUsername = (): Promise<void> => {
      return axios
        .patch(
          '/api/me/',
          { username: state.username.trim() },
          { headers: { 'Content-Type': 'application/json', ...authHeaders() } }
        )
        .then(() => undefined);
    };

    //画像を保存する（プロフィール未作成なら新規作成、作成済みなら更新）
    const saveAvatar = (): Promise<void> => {
      if (!state.avatarFile) {
        return Promise.resolve();
      }
      const formData = new FormData();
      formData.append('img', state.avatarFile);
      const headers = {
        'Content-Type': 'multipart/form-data',
        ...authHeaders(),
      };
      const request = state.profileId
        ? axios.patch(`/api/profiles/${state.profileId}/`, formData, { headers })
        : axios.post('/api/profiles/', formData, { headers });

      return request.then((req) => {
        state.profileId = req.data.id;
        state.avatarPreview = req.data.img || state.avatarPreview;
        state.avatarFile = null;
      });
    };

    //保存（表示名・画像をまとめて保存する）
    const save = (): void => {
      if (!state.username.trim()) {
        return;
      }
      state.saving = true;
      state.errorMessage = '';
      state.successMessage = '';

      saveUsername()
        .then(() => saveAvatar())
        .then(() => {
          state.successMessage = '保存しました。';
        })
        .catch((err) => {
          const data = err.response && err.response.data;
          const firstMessage =
            data && typeof data === 'object'
              ? (Object.values(data)[0] as unknown)
              : undefined;
          state.errorMessage = Array.isArray(firstMessage)
            ? String(firstMessage[0])
            : '保存に失敗しました。';
          console.error(err);
        })
        .finally(() => {
          state.saving = false;
        });
    };

    return { state, initial, onAvatarChange, save, MAX_AVATAR_SIZE_MB };
  },
});
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Yuji+Syuku&family=Shippori+Mincho:wght@500;700&display=swap');

.profile-page {
  min-height: calc(100vh - 150px);
  padding: 0 24px 60px;
  background: linear-gradient(180deg, #fbf8f0 0%, #f3ecd9 100%);
  font-family: 'Shippori Mincho', serif;
  color: #2b2621;
}

.profile-title {
  max-width: 480px;
  margin: 0 auto 24px;
  padding: 28px 4px 18px;
  font-family: 'Yuji Syuku', serif;
  font-size: 24px;
  letter-spacing: 6px;
  color: #6b3b2e;
  border-bottom: 1px solid #d8c9a3;
}

.profile-card {
  max-width: 480px;
  margin: 0 auto;
  padding: 28px 24px;
  background-color: #fffdf6;
  border: 1px solid #e3d9bd;
  border-radius: 4px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.06);
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.avatar-area {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
}

.avatar-preview {
  width: 96px;
  height: 96px;
  border-radius: 50%;
  overflow: hidden;
  background: #efe9dd;
  border: 1px solid #d8c9a3;
  display: flex;
  align-items: center;
  justify-content: center;
}

.avatar-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.avatar-placeholder {
  font-family: 'Yuji Syuku', serif;
  font-size: 32px;
  color: #a1876a;
}

.avatar-upload {
  position: relative;
  padding: 6px 16px;
  font-size: 12px;
  letter-spacing: 1px;
  color: #6b3b2e;
  border: 1px solid #b7a06a;
  border-radius: 999px;
  cursor: pointer;
}

.avatar-upload:hover {
  color: #9c2f24;
  border-color: #9c2f24;
}

.avatar-input {
  position: absolute;
  inset: 0;
  opacity: 0;
  cursor: pointer;
}

.avatar-hint {
  font-size: 11px;
  color: #8a7c62;
  letter-spacing: 0.5px;
}

.field-row {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.field-label {
  font-size: 12px;
  letter-spacing: 1px;
  color: #6b3b2e;
}

.field-input {
  box-sizing: border-box;
  padding: 10px 12px;
  border: 1px solid #d8c9a3;
  border-radius: 2px;
  background: #fffdf6;
  font-family: 'Shippori Mincho', serif;
  font-size: 15px;
  color: #2b2621;
  outline: none;
}

.form-message {
  font-size: 13px;
  letter-spacing: 1px;
}

.form-message.error {
  color: #9c2f24;
}

.form-message.success {
  color: #4a6b3b;
}

.actions {
  display: flex;
  justify-content: center;
}

.save-button {
  min-width: 140px;
  padding: 10px 28px;
  font-family: 'Yuji Syuku', serif;
  font-size: 15px;
  letter-spacing: 3px;
  color: #fbe9e4;
  background: linear-gradient(180deg, #b1453a 0%, #8a271d 100%);
  border: none;
  border-radius: 999px;
  cursor: pointer;
  box-shadow: 0 2px 5px rgba(0, 0, 0, 0.25);
  transition: transform 0.15s ease, box-shadow 0.15s ease, filter 0.15s ease;
}

.save-button:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.3);
  filter: brightness(1.05);
}

.save-button:disabled {
  background: #c9bfae;
  color: #efe9dd;
  cursor: not-allowed;
  box-shadow: none;
}
</style>
