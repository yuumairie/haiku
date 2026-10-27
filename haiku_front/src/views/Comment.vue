<template>
  <div class="comment-page">
    <div class="back-link" @click="goBack()">← 戻る</div>

    <div class="comment-card">
      <div class="label">論評を書く</div>
      <textarea
        id="text"
        v-model="state.text"
        class="comment-textarea"
        placeholder="この句への論評を入力"
        maxlength="100"
      ></textarea>
      <div class="char-count">{{ state.text.length }} / 100</div>
    </div>

    <div class="comment-actions">
      <button class="comment-button" :disabled="!state.text.trim()" @click="submit()">
        投稿する
      </button>
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent, reactive, computed } from 'vue';
import axios from 'axios';
import { useStore } from '../store';
import { useRouter } from '../router';

export default defineComponent({
  name: 'comment',
  setup() {
    const store = useStore();
    const router = useRouter();
    const haikuId = router.currentRoute.value.params.id;

    const state = reactive({
      text: '',
    });

    const jwt = computed(() => {
      return store.getters.getToken;
    });

    //どの一覧画面（home/mine）から来たか。クエリパラメータに無ければhome扱い。
    const listFrom = computed(() => {
      const from = router.currentRoute.value.query.from;
      return typeof from === 'string' && from ? from : 'home';
    });

    //戻る（コメント対象のdetail画面へ戻る）
    const goBack = () => {
      router.push({
        path: `/detail/${haikuId}`,
        query: { from: listFrom.value },
      });
    };

    //コメントを投稿する
    const submit = () => {
      if (!state.text.trim()) {
        return;
      }
      const data = {
        text: state.text,
        post: haikuId,
      };
      const headers = {
        'Content-Type': 'application/json',
        Authorization: `JWT ${jwt.value}`,
      };
      axios
        .post('api/comments/', data, { headers: headers })
        .then(() => {
          router.push({
            path: `/detail/${haikuId}`,
            query: { from: listFrom.value },
          });
        })
        .catch((err) => {
          console.error(err);
        });
    };

    return { state, goBack, submit, listFrom };
  },
});
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Yuji+Syuku&family=Shippori+Mincho:wght@500;700&display=swap');

.comment-page {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 30px 20px 60px;
  font-family: 'Shippori Mincho', serif;
  color: #3b332c;
}

.comment-page .back-link {
  align-self: flex-start;
  margin-left: calc(50% - 150px);
  margin-bottom: 16px;
  font-size: 13px;
  letter-spacing: 2px;
  color: #6b3b2e;
  cursor: pointer;
  border-bottom: 1px solid #b7a06a;
}

.comment-page .back-link:hover {
  color: #9c2f24;
  border-bottom-color: #9c2f24;
}

.comment-card {
  width: 300px;
  padding: 24px 20px;
  background-color: #faf6ea;
  background-image: repeating-linear-gradient(
      100deg,
      rgba(150, 130, 90, 0.05) 0px,
      rgba(150, 130, 90, 0.05) 1px,
      transparent 1px,
      transparent 7px
    ),
    linear-gradient(180deg, #fdfaf0 0%, #f6efdf 100%);
  border: 1px solid #d8c9a3;
  border-radius: 2px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.08), 0 10px 18px rgba(80, 60, 20, 0.12);
}

.comment-card .label {
  font-size: 13px;
  letter-spacing: 2px;
  color: #6b3b2e;
  margin-bottom: 12px;
}

.comment-textarea {
  box-sizing: border-box;
  width: 100%;
  min-height: 110px;
  resize: none;
  border: 1px solid #d8c9a3;
  border-radius: 2px;
  outline: none;
  background: #fffdf6;
  padding: 10px 12px;
  font-family: 'Shippori Mincho', serif;
  font-size: 15px;
  line-height: 1.7;
  color: #2b2621;
  caret-color: #a1372a;
}

.comment-textarea::placeholder {
  color: #b7a888;
}

.char-count {
  margin-top: 8px;
  text-align: right;
  font-size: 12px;
  color: #8a7c62;
  letter-spacing: 1px;
}

.comment-actions {
  margin-top: 22px;
}

.comment-button {
  min-width: 140px;
  padding: 10px 28px;
  font-family: 'Yuji Syuku', serif;
  font-size: 16px;
  letter-spacing: 3px;
  color: #fbe9e4;
  background: linear-gradient(180deg, #b1453a 0%, #8a271d 100%);
  border: none;
  border-radius: 999px;
  cursor: pointer;
  box-shadow: 0 2px 5px rgba(0, 0, 0, 0.25);
  transition: transform 0.15s ease, box-shadow 0.15s ease, filter 0.15s ease;
}

.comment-button:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.3);
  filter: brightness(1.05);
}

.comment-button:active:not(:disabled) {
  transform: translateY(0);
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.25);
}

.comment-button:disabled {
  background: #c9bfae;
  color: #efe9dd;
  cursor: not-allowed;
  box-shadow: none;
}
</style>
