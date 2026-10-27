<template>
  <div class="edit-page">
    <div class="back-link" @click="goBack()">← 戻る</div>

    <!-- 背景の装飾（梅の枝）。装飾目的のため読み上げ対象外 -->
    <svg class="deco-branch" viewBox="0 0 220 220" aria-hidden="true" focusable="false">
      <path
        d="M10 210 C 40 170, 60 140, 70 110 S 100 60, 150 20"
        fill="none"
        stroke="currentColor"
        stroke-width="3"
        stroke-linecap="round"
      />
      <path
        d="M70 110 C 85 95, 95 90, 115 85"
        fill="none"
        stroke="currentColor"
        stroke-width="2"
        stroke-linecap="round"
      />
      <path
        d="M95 70 C 105 60, 112 55, 128 48"
        fill="none"
        stroke="currentColor"
        stroke-width="2"
        stroke-linecap="round"
      />
      <circle cx="150" cy="20" r="7" />
      <circle cx="128" cy="48" r="6" />
      <circle cx="115" cy="85" r="5" />
      <circle cx="166" cy="34" r="5" />
      <circle cx="138" cy="60" r="4" />
    </svg>

    <div class="tanzaku">
      <textarea
        id="content"
        :value="state.haikuContent"
        class="tanzaku-textarea"
        :style="textareaStyle"
        placeholder="ここに一句"
        @input="onInput"
      ></textarea>
    </div>

    <div class="char-count">{{ contentLength }} / 50</div>

    <div class="kigo-section">
      <div class="kigo-row">
        <label class="kigo-label" for="kigo">季語</label>
        <input
          id="kigo"
          v-model="state.kigo"
          type="text"
          class="kigo-input"
          placeholder="（任意）句に含まれる季語"
        />
      </div>
      <div class="kigo-row">
        <label class="season-label" for="season">季節</label>
        <select id="season" v-model="state.season" class="season-select">
          <option value="">未設定</option>
          <option value="春">春</option>
          <option value="夏">夏</option>
          <option value="秋">秋</option>
          <option value="冬">冬</option>
          <option value="新年">新年</option>
        </select>
      </div>
    </div>
    <div v-if="state.kigoError" class="kigo-error">{{ state.kigoError }}</div>

    <div class="post-actions">
      <button class="post-button" :disabled="!contentLength" @click="update()">更新</button>
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent, reactive, computed, onMounted } from 'vue';
import { useStore } from '../store';
import { useRouter } from '../router';
import axios from 'axios';

// 短冊は五・七・五の3行を想定しているため、入力できる行数を3行までに制限する。
// 文字数の上限（50文字）は改行を含めずに数える（改行は行の区切りであって句の文字では
// ないため）。
const MAX_LINES = 3;
const MAX_CHARS = 50;

const limitContent = (text: string): string => {
  let lines = text.split('\n');
  if (lines.length > MAX_LINES) {
    lines = lines.slice(0, MAX_LINES);
  }

  let remaining = MAX_CHARS;
  const limitedLines = lines.map((line) => {
    if (remaining <= 0) {
      return '';
    }
    if (line.length > remaining) {
      const cut = line.slice(0, remaining);
      remaining = 0;
      return cut;
    }
    remaining -= line.length;
    return line;
  });

  return limitedLines.join('\n');
};

export default defineComponent({
  setup() {
    const store = useStore();
    const router = useRouter();
    const state = reactive({
      haikuContent: '',
      // 季語・季節は投稿時はサーバー側で自動判定されるが、ここで編集できる
      kigo: '',
      season: '',
      kigoError: '',
    });

    //JWT
    const jwt = computed(() => {
      return store.getters.getToken;
    });

    //どの一覧画面（home/mine）から来たか。クエリパラメータに無ければhome扱い。
    const listFrom = computed(() => {
      const from = router.currentRoute.value.query.from;
      return typeof from === 'string' && from ? from : 'home';
    });

    //入力文字数（句のボリューム表示用。改行は含めない）
    const contentLength = computed(() => state.haikuContent.replace(/\n/g, '').length);

    //入力されている行数（1〜MAX_LINES）
    const lineCount = computed(() => {
      const count = state.haikuContent.split('\n').length;
      return Math.min(Math.max(count, 1), MAX_LINES);
    });

    //左右に同じ余白(padding)を入れて、文字の列だけを横方向の中央に寄せる。
    //textarea自体の幅は変えないので、クリックできる範囲は短冊の全幅のまま。
    const textareaStyle = computed(() => {
      const usedWidth = `${lineCount.value * 2.1}em`;
      const sidePadding = `calc((100% - ${usedWidth}) / 2)`;
      return {
        paddingLeft: sidePadding,
        paddingRight: sidePadding,
      };
    });

    //入力を監視し、4行目以降・51文字目以降（改行を除く）は入力できないようにする
    const onInput = (event: Event) => {
      const textarea = event.target as HTMLTextAreaElement;
      const limited = limitContent(textarea.value);
      state.haikuContent = limited;
      if (textarea.value !== limited) {
        // 制限を超えた分を取り除いて表示にも反映する
        textarea.value = limited;
      }
    };

    onMounted(() => {
      axios
        .get(`api/haikus/${router.currentRoute.value.params.id}/`)
        .then((req) => {
          state.haikuContent = limitContent(req.data.content);
          state.kigo = req.data.kigo || '';
          state.season = req.data.season || '';
        })
        .catch((err) => {
          console.error(err);
        });
    });

    //戻る（編集対象のdetail画面へ戻る）
    const goBack = () => {
      router.push({
        path: `/detail/${router.currentRoute.value.params.id}`,
        query: { from: listFrom.value },
      });
    };

    //更新関数
    const update = () => {
      if (!state.haikuContent.trim()) {
        return;
      }
      state.kigoError = '';
      const data = {
        content: state.haikuContent,
        kigo: state.kigo.trim() || null,
        season: state.season || null,
      };
      const headers = {
        'Content-Type': 'application/json',
        Authorization: `JWT ${jwt.value}`,
      };

      axios
        .patch(`api/haikus/${router.currentRoute.value.params.id}/`, data, {
          headers: headers,
        })
        .then(() => {
          router.push({
            path: `/detail/${router.currentRoute.value.params.id}`,
            query: { from: listFrom.value },
          });
        })
        .catch((err) => {
          // 季語が本文に含まれていない場合などのサーバー側エラーを表示する
          const kigoMessage = err.response && err.response.data && err.response.data.kigo;
          state.kigoError = Array.isArray(kigoMessage) ? kigoMessage[0] : '更新に失敗しました。';
          console.error(err);
        });
    };
    return { state, update, jwt, contentLength, onInput, textareaStyle, goBack, listFrom };
  },
});
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Yuji+Syuku&family=Shippori+Mincho:wght@500;700&display=swap');

.edit-page {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 30px 20px 60px;
  font-family: 'Shippori Mincho', serif;
  color: #3b332c;
}

.edit-page .back-link {
  position: relative;
  z-index: 1;
  align-self: flex-start;
  margin-left: calc(50% - 110px);
  margin-bottom: 16px;
  font-size: 13px;
  letter-spacing: 2px;
  color: #6b3b2e;
  cursor: pointer;
  border-bottom: 1px solid #b7a06a;
}

.edit-page .back-link:hover {
  color: #9c2f24;
  border-bottom-color: #9c2f24;
}

/* 背景の梅の枝（墨色、淡く） */
.deco-branch {
  position: absolute;
  top: -10px;
  right: 6%;
  width: 150px;
  height: 150px;
  color: #3b332c;
  opacity: 0.12;
  fill: #3b332c;
  pointer-events: none;
  z-index: 0;
}

/* 短冊（たんざく）本体：和紙風の縦長の紙 */
.tanzaku {
  position: relative;
  z-index: 1;
  width: 220px;
  min-height: 380px;
  padding: 28px 18px 24px;
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
  transform: rotate(-0.6deg);
  display: flex;
  flex-direction: column;
  align-items: center;
}

/* 吊り紐っぽい上部のアクセント */
.tanzaku::before {
  content: '';
  position: absolute;
  top: -10px;
  left: 50%;
  width: 2px;
  height: 14px;
  background: #b7a06a;
  transform: translateX(-50%);
}

.tanzaku-textarea {
  writing-mode: vertical-rl;
  text-orientation: upright;
  text-align: center;
  box-sizing: border-box;
  flex: 1;
  width: 100%;
  min-height: 260px;
  resize: none;
  border: none;
  outline: none;
  background: transparent;
  font-family: 'Shippori Mincho', serif;
  font-size: 22px;
  line-height: 2.1;
  letter-spacing: 4px;
  color: #2b2621;
  caret-color: #a1372a;
}

.tanzaku-textarea::placeholder {
  color: #b7a888;
}

.char-count {
  margin-top: 10px;
  font-size: 12px;
  color: #8a7c62;
  letter-spacing: 1px;
}

.kigo-section {
  margin-top: 16px;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 10px;
}

.kigo-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.kigo-label,
.season-label {
  width: 32px;
  font-size: 12px;
  color: #6b3b2e;
  letter-spacing: 1px;
}

.kigo-input {
  width: 110px;
  padding: 4px 8px;
  font-family: 'Shippori Mincho', serif;
  font-size: 13px;
  color: #2b2621;
  background: #fffdf6;
  border: 1px solid #d8c9a3;
  border-radius: 3px;
  outline: none;
}

.season-select {
  padding: 4px 6px;
  font-family: 'Shippori Mincho', serif;
  font-size: 13px;
  color: #2b2621;
  background: #fffdf6;
  border: 1px solid #d8c9a3;
  border-radius: 3px;
  outline: none;
}

.kigo-error {
  margin-top: 8px;
  font-size: 12px;
  color: #9c2f24;
  letter-spacing: 1px;
}

.post-actions {
  margin-top: 22px;
}

.post-button {
  min-width: 120px;
  padding: 10px 28px;
  font-family: 'Yuji Syuku', serif;
  font-size: 18px;
  letter-spacing: 4px;
  color: #fbe9e4;
  background: linear-gradient(180deg, #b1453a 0%, #8a271d 100%);
  border: none;
  border-radius: 999px;
  cursor: pointer;
  box-shadow: 0 2px 5px rgba(0, 0, 0, 0.25);
  transition: transform 0.15s ease, box-shadow 0.15s ease, filter 0.15s ease;
}

.post-button:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.3);
  filter: brightness(1.05);
}

.post-button:active:not(:disabled) {
  transform: translateY(0);
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.25);
}

.post-button:disabled {
  background: #c9bfae;
  color: #efe9dd;
  cursor: not-allowed;
  box-shadow: none;
}
</style>
