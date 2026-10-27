<template>
  <div class="detail-page">
    <div class="back-link" @click="goBack()">← 戻る</div>

    <div class="tanzaku" :class="seasonClass">
      <div class="content">{{ state.haiku.content }}</div>
      <div class="poster-name" @click="goToProfile()">
        <img
          v-if="state.haiku.userPost.avatar"
          :src="state.haiku.userPost.avatar"
          class="poster-avatar"
        />
        <span class="poster-name-text">{{ state.haiku.userPost.username || '匿名' }}</span>
      </div>
    </div>

    <div v-if="state.haiku.kigo" class="kigo-badge">
      季語: {{ state.haiku.kigo }}（{{ state.haiku.season }}）
    </div>

    <div v-if="state.haiku.isPublic === false" class="visibility-badge">
      非公開（自分のみ閲覧可）
    </div>

    <div
      v-if="jwt && state.haiku.userPost.id !== userId"
      class="follow-badge"
      :class="{ following: isFollowing }"
      @click="toggleFollow()"
    >
      {{ isFollowing ? '購読中' : '+読者になる' }}
    </div>

    <div class="actions" v-if="state.haiku.userPost.id === userId">
      <div class="edit" @click="edit()">編集する</div>
      <div class="delete" @click="deleteHaiku()">削除する</div>
    </div>

    <div class="comments-section">
      <div class="comments-header">
        <span class="comments-title">論評</span>
        <router-link
          v-if="jwt"
          :to="{ path: `/comment/${state.haiku.id}`, query: { from: listFrom } }"
          class="comment-link"
        >
          論評する
        </router-link>
      </div>

      <div v-if="state.comments.length" class="comment-list">
        <div v-for="comment in state.comments" :key="comment.id" class="comment-item">
          <span class="comment-user">{{ comment.userComment.username }}</span>
          <span class="comment-text">{{ comment.text }}</span>
        </div>
      </div>
      <div v-else class="comment-empty">まだ論評はありません。</div>
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent, onMounted, reactive, computed } from 'vue';
import axios from 'axios';
import { ActionTypes, useStore } from '../store';
import { useRouter } from '../router';
import { CommentModel, FollowModel, HaikuModel } from '../types/task';

export default defineComponent({
  name: 'detail',
  setup() {
    const store = useStore();
    const router = useRouter();

    const state = reactive({
      // content/createdAt/goodは任意項目のためここでは初期化せず、
      // APIから取得した実データで埋める
      // （snake_case⇄camelCaseの変換はaxiosのインターセプタ(main.ts)が行うため、
      //  ここではAPIのキー名を気にせずcamelCaseだけを書けばよい）
      haiku: {
        id: 0,
        userPost: {
          id: 0,
          username: '',
        },
      } as HaikuModel,
      comments: [] as CommentModel[],
    });
    const jwt = computed(() => {
      return store.getters.getToken;
    });
    const userId = computed(() => {
      return store.getters.getUserId;
    });
    //どの一覧画面（home/mine）から来たか。クエリパラメータに無ければhome扱い。
    const listFrom = computed(() => {
      const from = router.currentRoute.value.query.from;
      return typeof from === 'string' && from ? from : 'home';
    });

    const followList = computed<Array<FollowModel>>(() => {
      return store.getters.getFollowList;
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
      const season = state.haiku.season;
      return (season && SEASON_CLASS_MAP[season]) || '';
    });

    //この句の投稿者をすでにフォローしているかどうか
    const isFollowing = computed<boolean>(() => {
      return followList.value.some((follow) => follow.following.id === state.haiku.userPost.id);
    });

    //フォロー・フォロー解除を切り替える
    const toggleFollow = (): void => {
      const targetId = state.haiku.userPost.id;
      const headers = {
        'Content-Type': 'application/json',
        Authorization: `JWT ${jwt.value}`,
      };
      if (isFollowing.value) {
        const follow = followList.value.find((f) => f.following.id === targetId);
        if (!follow) {
          return;
        }
        axios
          .delete(`api/follows/${follow.id}/`, { headers: headers })
          .then(() => {
            store.dispatch(ActionTypes.FOLLOW_LIST);
          })
          .catch((err) => {
            console.error(err);
          });
      } else {
        axios
          .post('api/follows/', { following: targetId }, { headers: headers })
          .then(() => {
            store.dispatch(ActionTypes.FOLLOW_LIST);
          })
          .catch((err) => {
            console.error(err);
          });
      }
    };
    //コメント一覧を取得する
    const getComments = (): void => {
      axios
        .get('api/comments/', {
          params: { post: router.currentRoute.value.params.id },
        })
        .then((req) => {
          state.comments = req.data;
        })
        .catch((err) => {
          console.error(err);
        });
    };

    onMounted(() => {
      axios
        .get(`api/haikus/${router.currentRoute.value.params.id}/`)
        .then((req) => {
          state.haiku = req.data;
        })
        .catch((err) => {
          console.error(err);
        });
      getComments();
    });
    const edit = () => {
      router.push({
        path: `/edit/${router.currentRoute.value.params.id}`,
        query: { from: listFrom.value },
      });
    };

    //投稿者名をクリックしたらそのユーザのプロフィール（俳句一覧）画面へ遷移する
    const goToProfile = (): void => {
      router.push({
        path: `/user/${state.haiku.userPost.id}`,
        query: { from: router.currentRoute.value.fullPath },
      });
    };

    //戻る（元の一覧画面へ戻る）
    const goBack = () => {
      router.push(`/${listFrom.value}`);
    };

    //削除
    const deleteHaiku = () => {
      if (!window.confirm('この句を削除しますか？')) {
        return;
      }
      const headers = {
        'Content-Type': 'application/json',
        Authorization: `JWT ${jwt.value}`,
      };
      axios
        .delete(`api/haikus/${router.currentRoute.value.params.id}/`, {
          headers: headers,
        })
        .then(() => {
          router.push('/home');
        })
        .catch((err) => {
          console.error(err);
        });
    };

    return {
      state,
      jwt,
      userId,
      listFrom,
      isFollowing,
      toggleFollow,
      edit,
      deleteHaiku,
      goBack,
      getComments,
      goToProfile,
      seasonClass,
    };
  },
});
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Yuji+Syuku&family=Shippori+Mincho:wght@500;700&display=swap');

.detail-page {
  position: relative;
  margin-top: 10px;
  padding-bottom: 60px;
  display: flex;
  flex-direction: column;
  align-items: center;
  font-family: 'Shippori Mincho', serif;
  color: #2b2621;
}

.detail-page .back-link {
  align-self: flex-start;
  margin-left: calc(50% - 120px);
  margin-bottom: 20px;
  font-size: 13px;
  letter-spacing: 2px;
  color: #6b3b2e;
  cursor: pointer;
  border-bottom: 1px solid #b7a06a;
}

.detail-page .back-link:hover {
  color: #9c2f24;
  border-bottom-color: #9c2f24;
}

/* 短冊（たんざく）風の表示 */
.detail-page .tanzaku {
  position: relative;
  width: 240px;
  min-height: 320px;
  padding: 32px 20px 24px;
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
  display: flex;
  justify-content: center;
}

/* 季節ごとの短冊の色味。文字が読みやすいよう、淡いトーンで全体の雰囲気だけ変える */
.detail-page .tanzaku.season-spring {
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

.detail-page .tanzaku.season-summer {
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

.detail-page .tanzaku.season-autumn {
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

.detail-page .tanzaku.season-winter {
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

.detail-page .tanzaku.season-newyear {
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
.detail-page .tanzaku::before {
  content: '';
  position: absolute;
  top: -10px;
  left: 50%;
  width: 2px;
  height: 14px;
  background: #b7a06a;
  transform: translateX(-50%);
}

.detail-page .content {
  writing-mode: vertical-rl;
  text-orientation: upright;
  /* 投稿時の改行（五・七・五の区切り）はそのまま保持しつつ、
     それ以外の折り返しは発生させない */
  white-space: pre;
  text-align: center;
  font-size: 24px;
  line-height: 2.2;
  letter-spacing: 5px;
}

.detail-page .post-no {
  margin-top: 16px;
  font-size: 13px;
  color: #9c2f24;
  font-weight: 700;
  letter-spacing: 1px;
}

.detail-page .kigo-badge {
  margin-top: 10px;
  font-size: 12px;
  letter-spacing: 1px;
  color: #4a6b3b;
  background: #eef3e6;
  border: 1px solid #c9d8bb;
  border-radius: 999px;
  padding: 3px 10px;
  white-space: nowrap;
}

.detail-page .visibility-badge {
  margin-top: 10px;
  font-size: 12px;
  letter-spacing: 1px;
  color: #6b5d45;
  background: #efe9dd;
  border: 1px solid #d8c9a3;
  border-radius: 999px;
  padding: 3px 10px;
  white-space: nowrap;
}

.detail-page .poster-name {
  position: absolute;
  left: 16px;
  bottom: 14px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 5px;
  cursor: pointer;
}

.detail-page .poster-avatar {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  object-fit: cover;
  border: 1px solid #d8c9a3;
}

.detail-page .poster-name-text {
  writing-mode: vertical-rl;
  text-orientation: upright;
  font-size: 13px;
  letter-spacing: 3px;
  color: #6b5d45;
  white-space: nowrap;
}

.detail-page .poster-name:hover .poster-name-text {
  color: #9c2f24;
}

.detail-page .follow-badge {
  margin-top: 14px;
  padding: 3px 10px;
  font-size: 11px;
  letter-spacing: 1px;
  color: #fbe9e4;
  background: linear-gradient(180deg, #b1453a 0%, #8a271d 100%);
  border-radius: 999px;
  cursor: pointer;
  white-space: nowrap;
}

.detail-page .follow-badge.following {
  color: #6b3b2e;
  background: #efe9dd;
  border: 1px solid #d8c9a3;
}

.detail-page .actions {
  margin-top: 18px;
  display: flex;
  align-items: center;
  gap: 18px;
}

.detail-page .edit {
  cursor: pointer;
  font-size: 13px;
  letter-spacing: 1px;
  color: blue;
  border-bottom: 1px solid #9c2f24;
}

.detail-page .delete {
  cursor: pointer;
  font-size: 13px;
  letter-spacing: 1px;
  color: #9c2f24;
  border-bottom: 1px solid #9c2f24;
}

.detail-page .delete:hover {
  opacity: 0.75;
}

.detail-page .comments-section {
  margin-top: 28px;
  width: 280px;
}

.detail-page .comments-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding-bottom: 8px;
  border-bottom: 1px solid #d8c9a3;
}

.detail-page .comments-title {
  font-size: 14px;
  letter-spacing: 2px;
  color: #6b3b2e;
}

.detail-page .comment-link {
  font-size: 12px;
  letter-spacing: 1px;
  color: #6b3b2e;
  text-decoration: none;
  border-bottom: 1px solid #b7a06a;
  white-space: nowrap;
}

.detail-page .comment-link:hover {
  color: #9c2f24;
  border-bottom-color: #9c2f24;
}

.detail-page .comment-list {
  margin-top: 12px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.detail-page .comment-item {
  padding: 10px 12px;
  background-color: #fffdf6;
  border: 1px solid #e3d9bd;
  border-radius: 2px;
  font-size: 13px;
  line-height: 1.6;
}

.detail-page .comment-user {
  display: block;
  margin-bottom: 4px;
  font-size: 11px;
  letter-spacing: 1px;
  color: #9c2f24;
}

.detail-page .comment-text {
  display: block;
  color: #2b2621;
  white-space: pre-line;
  word-break: break-all;
}

.detail-page .comment-empty {
  margin-top: 16px;
  font-size: 13px;
  color: #8a7c62;
  text-align: center;
}
</style>
