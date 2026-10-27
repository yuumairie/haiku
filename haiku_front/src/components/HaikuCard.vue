<template>
  <div class="haiku" :class="seasonClass">
    <div class="content" ref="contentRef" @click="clickContent(haiku.id)">
      <div class="main" :style="mainStyle">{{ haiku.content }}</div>
      <div class="poster-name" @click.stop="goToProfile(haiku.userPost.id)">
        <img v-if="haiku.userPost.avatar" :src="haiku.userPost.avatar" class="poster-avatar" />
        <span class="poster-name-text">
          {{ haiku.userPost.username ? haiku.userPost.username : '匿名' }}
        </span>
      </div>
    </div>
    <div class="footer">
      <div class="meta">
        <span class="time">{{ haiku.created_at }}</span>
      </div>
      <div class="good-area">
        <span class="heart" v-if="isNotLoginUser">
          <img
            class="heart-img"
            :src="require('@/assets/images/good.png')"
            @click="clickGood(false, haiku.id, haiku.good)"
            v-if="isAlreadyGood(haiku.good)"
          />
          <img
            class="heart-img"
            :src="require('@/assets/images/normal.png')"
            @click="clickGood(true, haiku.id)"
            v-else
          />
        </span>
        <span class="count">{{ haiku.good.length }}</span>
        <span class="good-label"> ゆかし</span>
      </div>
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent, computed, reactive, ref, onMounted, nextTick, watch } from 'vue';
import { useRouter } from '../router';
import { ActionTypes, useStore } from '../store';
import axios from 'axios';
import { UserModel, GoodModel } from '../types/task.d';

export default defineComponent({
  name: 'HaikuCard',
  props: {
    haiku: {
      type: Object,
      required: true,
    },
    isNotLoginUser: Boolean,
    //どの一覧画面から表示されているか（'home' or 'mine'）。
    //詳細画面の「戻る」が元の一覧に戻れるようにするために渡す。
    listFrom: {
      type: String,
      default: 'home',
    },
  },
  emits: ['get-haiku-list'],
  setup(props, { emit }) {
    const router = useRouter();
    const store = useStore();
    const state = reactive({
      userId: store.getters.getUserId,
    });

    // 季節ごとに短冊の色味を変えるためのクラス名
    const SEASON_CLASS_MAP: Record<string, string> = {
      春: 'season-spring',
      夏: 'season-summer',
      秋: 'season-autumn',
      冬: 'season-winter',
      新年: 'season-newyear',
    };
    const seasonClass = computed<string>(() => {
      const season = (props.haiku as { season?: string }).season;
      return (season && SEASON_CLASS_MAP[season]) || '';
    });

    // カードの高さを固定しているため、一番長い行の文字数に応じて
    // フォントサイズを縮小し、はみ出さずに収まるようにする。
    // 「.content に実際に収まる高さ」はDOMから直接計測する（固定値で
    // 見積もると、フッターの実際の高さとズレて余白が目立つため）。
    const MAIN_MAX_FONT_SIZE = 19;
    const MAIN_MIN_FONT_SIZE = 9;
    const LETTER_SPACING_RATIO = 0.16;
    // 縦書きで1文字が縦方向に必要な高さ ≒ font-size * この係数
    // （line-heightは縦書きでは「行(列)の太さ」＝横方向にしか影響しないため
    // 使わない。実測で font-size の約1.03倍だったため少し余裕を持たせる）
    const VERTICAL_ADVANCE_RATIO = 1.05;
    const SAFETY_MARGIN = 0.95; // 計測・フォントの誤差に備えた余裕

    const contentRef = ref<HTMLElement | null>(null);
    const mainFontSize = ref(MAIN_MAX_FONT_SIZE);

    const recalcMainFontSize = (): void => {
      const el = contentRef.value;
      if (!el) {
        return;
      }
      const text = (props.haiku as { content?: string }).content || '';
      const lines = text.split('\n');
      const maxLineLength = Math.max(1, ...lines.map((line) => line.length));
      const paddingBottom = parseFloat(getComputedStyle(el).paddingBottom || '0');
      const availableHeight = (el.clientHeight - paddingBottom) * SAFETY_MARGIN;
      const perCharHeight = VERTICAL_ADVANCE_RATIO + LETTER_SPACING_RATIO;
      const fitSize = Math.floor(availableHeight / (maxLineLength * perCharHeight));
      mainFontSize.value = Math.max(MAIN_MIN_FONT_SIZE, Math.min(MAIN_MAX_FONT_SIZE, fitSize));
    };

    onMounted(() => {
      nextTick(recalcMainFontSize);
    });
    // 編集などで同じカード（同じid）の内容が更新された場合も再計算する
    watch(
      () => (props.haiku as { content?: string }).content,
      () => nextTick(recalcMainFontSize)
    );

    const mainStyle = computed(() => ({
      fontSize: `${mainFontSize.value}px`,
      // 文字が小さくなっても字間の見た目の比率が変わらないようにする
      letterSpacing: `${(mainFontSize.value * LETTER_SPACING_RATIO).toFixed(1)}px`,
    }));

    const goodList = computed<Array<GoodModel>>(() => {
      return store.getters.getGoodList;
    });

    const clickContent = (id: number) => {
      router.push({ path: `/detail/${id}`, query: { from: props.listFrom } });
    };

    //投稿者名をクリックしたらそのユーザのプロフィール（俳句一覧）画面へ遷移する
    const goToProfile = (userId: number): void => {
      router.push({
        path: `/user/${userId}`,
        query: { from: router.currentRoute.value.fullPath },
      });
    };

    const isAlreadyGood = (goodUserList: Array<UserModel>): boolean => {
      return goodUserList.some((user: UserModel) => {
        return user.id === state.userId;
      });
    };

    const getMyGood = (userId: string, haikuId: string): number => {
      const good: GoodModel | undefined = goodList.value.find((good) => {
        return good.user === userId && good.haiku === haikuId;
      });
      if (good) {
        return good.id;
      }
      return 0;
    };

    const clickGood = (isGood: boolean, id: string, goodUserList?: Array<UserModel>): void => {
      const data = {
        user: state.userId,
        haiku: id,
      };
      const headers = {
        'Content-Type': 'application/json',
        Authorization: `JWT ${store.getters.getToken}`,
      };
      if (isGood) {
        axios
          .post('api/goods/', data, {
            headers: headers,
          })
          .then((resp) => {
            //ユーザのいいね一覧取得
            store.dispatch(ActionTypes.GOOD);
            emit('get-haiku-list');
          })
          .catch((err) => {
            console.error(err);
          });
      } else {
        axios
          .delete(`api/goods/${getMyGood(state.userId, id)}/`, {
            headers: headers,
          })
          .then((resp) => {
            //ユーザのいいね一覧取得
            store.dispatch(ActionTypes.GOOD);
            emit('get-haiku-list');
          })
          .catch((err) => {
            console.error(err);
          });
      }
    };
    return {
      clickContent,
      clickGood,
      isAlreadyGood,
      goToProfile,
      seasonClass,
      mainStyle,
      contentRef,
    };
  },
});
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Yuji+Syuku&family=Shippori+Mincho:wght@500;700&display=swap');

/* 短冊（たんざく）風のカード */
.haiku {
  position: relative;
  width: 160px;
  /* 句の長さによらずカードの高さを揃える */
  height: 300px;
  margin: 16px 16px 0;
  padding: 24px 10px 14px;
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
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.08), 0 8px 14px rgba(80, 60, 20, 0.12);
  transform: rotate(-0.5deg);
  display: flex;
  flex-direction: column;
  align-items: center;
  font-family: 'Shippori Mincho', serif;
  color: #2b2621;
}

/* 季節ごとの短冊の色味。文字が読みやすいよう、淡いトーンで全体の雰囲気だけ変える */
.haiku.season-spring {
  background-color: #fdf2f5;
  background-image: repeating-linear-gradient(
      100deg,
      rgba(150, 130, 90, 0.05) 0px,
      rgba(150, 130, 90, 0.05) 1px,
      transparent 1px,
      transparent 7px
    ),
    linear-gradient(180deg, #fdf3f6 0%, #fbe1e8 100%);
  border-color: #e3b8c6;
}

.haiku.season-summer {
  background-color: #f2f9f1;
  background-image: repeating-linear-gradient(
      100deg,
      rgba(150, 130, 90, 0.05) 0px,
      rgba(150, 130, 90, 0.05) 1px,
      transparent 1px,
      transparent 7px
    ),
    linear-gradient(180deg, #f3f9ee 0%, #e0eed9 100%);
  border-color: #b7d6ac;
}

.haiku.season-autumn {
  background-color: #fdf1e2;
  background-image: repeating-linear-gradient(
      100deg,
      rgba(150, 130, 90, 0.05) 0px,
      rgba(150, 130, 90, 0.05) 1px,
      transparent 1px,
      transparent 7px
    ),
    linear-gradient(180deg, #fbe9d2 0%, #f0c799 100%);
  border-color: #d99b4c;
}

.haiku.season-winter {
  background-color: #f0f6fa;
  background-image: repeating-linear-gradient(
      100deg,
      rgba(150, 130, 90, 0.05) 0px,
      rgba(150, 130, 90, 0.05) 1px,
      transparent 1px,
      transparent 7px
    ),
    linear-gradient(180deg, #f1f7fb 0%, #dce9f2 100%);
  border-color: #a9c8db;
}

.haiku.season-newyear {
  background-color: #fff7e2;
  background-image: repeating-linear-gradient(
      100deg,
      rgba(150, 130, 90, 0.05) 0px,
      rgba(150, 130, 90, 0.05) 1px,
      transparent 1px,
      transparent 7px
    ),
    linear-gradient(180deg, #fff3cf 0%, #f6dd9b 100%);
  border-color: #d4af37;
}

/* 吊り紐っぽい上部のアクセント */
.haiku::before {
  content: '';
  position: absolute;
  top: -9px;
  left: 50%;
  width: 2px;
  height: 13px;
  background: #b7a06a;
  transform: translateX(-50%);
}

.haiku .content {
  position: relative;
  flex: 1;
  width: 100%;
  display: flex;
  justify-content: center;
  align-items: flex-start;
  cursor: pointer;
  padding-bottom: 10px;
  margin-bottom: 8px;
  border-bottom: 1px double #c9b98f;
  overflow: hidden; /* 高さを固定したため、長い句はここで切り詰める */
}

.haiku .poster-name {
  position: absolute;
  left: 2px;
  bottom: 4px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 3px;
  cursor: pointer;
}

.haiku .poster-avatar {
  width: 16px;
  height: 16px;
  border-radius: 50%;
  object-fit: cover;
  border: 1px solid #d8c9a3;
}

.haiku .poster-name-text {
  writing-mode: vertical-rl;
  text-orientation: upright;
  font-size: 11px;
  letter-spacing: 2px;
  color: #6b5d45;
  white-space: nowrap;
}

.haiku .poster-name:hover .poster-name-text {
  color: #9c2f24;
}

.haiku .main {
  writing-mode: vertical-rl;
  text-orientation: upright;
  /* 投稿時の改行（五・七・五の区切り）はそのまま保持する。
     font-size/letter-spacingは句の長さに応じてJS側(mainStyle)で動的に指定する */
  white-space: pre;
  line-height: 2;
  padding: 2px 4px;
}

.footer {
  width: 100%;
  font-family: 'Shippori Mincho', serif;
}

.footer .meta {
  display: flex;
  /* 分まで表示すると幅が増えるため、狭いカードでは折り返せるようにする */
  flex-wrap: wrap;
  align-items: center;
  gap: 2px 6px;
  font-size: 11px;
  color: #6b5d45;
  margin-bottom: 8px;
}

.footer .time {
  flex-shrink: 0;
  /* 折り返した場合でも右端に揃えて表示する */
  margin-left: auto;
  font-size: 10px;
}

.good-area {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
}

.heart-img {
  height: 18px;
  cursor: pointer;
  vertical-align: middle;
}

.good-label {
  font-family: 'Yuji Syuku', serif;
  font-size: 12px;
  color: #9c2f24;
}

.good-area .count {
  font-weight: 700;
  color: #9c2f24;
  font-size: 13px;
}
</style>
