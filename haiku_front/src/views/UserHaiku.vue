<template>
  <div class="user-haiku">
    <div class="back-link" @click="goBack()">← 戻る</div>

    <div class="user-haiku-header">
      <h2 class="user-haiku-title">{{ displayName }}の句</h2>
      <div class="follow-area">
        <span class="follower-count">読者 {{ state.followerCount }}人</span>
        <button
          v-if="jwt && isNotLoginUser"
          class="follow-button"
          :class="{ following: state.isFollowing }"
          @click="toggleFollow()"
        >
          {{ state.isFollowing ? '購読中' : '読者になる' }}
        </button>
      </div>
    </div>

    <div v-if="state.haikuList.length" class="cards">
      <div v-for="haiku in state.haikuList" :key="haiku.id">
        <Haiku-Card
          :haiku="haiku"
          :isNotLoginUser="isNotLoginUser"
          list-from="search"
          @get-haiku-list="getHaikuList"
        />
      </div>
    </div>
    <div v-else class="empty-state">まだこのユーザの句が投稿されていません。</div>
  </div>
</template>

<script lang="ts">
import { defineComponent, onMounted, reactive, computed } from 'vue';
import axios from 'axios';
import HaikuCard from '../components/HaikuCard.vue';
import { ActionTypes, useStore } from '../store';
import { useRouter } from '../router';
import { HaikuModel, FollowModel } from '../types/task';

export default defineComponent({
  name: 'user-haiku',
  components: {
    HaikuCard,
  },
  setup() {
    const store = useStore();
    const router = useRouter();
    const targetUserId = router.currentRoute.value.params.id;

    const state = reactive({
      haikuList: [] as HaikuModel[],
      followerCount: 0,
      isFollowing: false,
      followId: 0,
    });

    const jwt = computed(() => {
      return store.getters.getToken;
    });

    //自分自身のページを見ている場合は「ゆかし」ボタンを出さない
    const isNotLoginUser = computed<boolean>(() => {
      if (jwt.value) {
        return String(store.getters.getUserId) !== String(targetUserId);
      }
      return false;
    });

    //取得した句から表示名を決める（句が無い場合は汎用的な表示にする）
    const displayName = computed(() => {
      if (state.haikuList.length) {
        return state.haikuList[0].userPost.username || '匿名';
      }
      return 'このユーザ';
    });

    const getHaikuList = (): void => {
      axios
        .get('/api/haikus/', { params: { userPost: targetUserId } })
        .then((req) => {
          state.haikuList = req.data;
        })
        .catch((err) => {
          console.error(err);
        });
    };

    //フォロワー数と、自分がすでにフォローしているかどうかを取得する
    const getFollowState = (): void => {
      axios
        .get('/api/follows/', { params: { following: targetUserId } })
        .then((req) => {
          state.followerCount = req.data.length;
          if (jwt.value) {
            const myFollow = req.data.find(
              (follow: FollowModel) =>
                String(follow.follower.id) === String(store.getters.getUserId)
            );
            state.isFollowing = Boolean(myFollow);
            state.followId = myFollow ? myFollow.id : 0;
          }
        })
        .catch((err) => {
          console.error(err);
        });
    };

    //フォロー・フォロー解除を切り替える。
    //ホーム画面の「購読中」タブなどが参照する、ログイン中ユーザ全体の
    //フォロー一覧（Vuexストア）もここで更新しておかないと、一覧画面に
    //戻った時にフォロー結果が反映されない
    const toggleFollow = (): void => {
      const headers = {
        'Content-Type': 'application/json',
        Authorization: `JWT ${jwt.value}`,
      };
      if (state.isFollowing) {
        axios
          .delete(`api/follows/${state.followId}/`, { headers: headers })
          .then(() => {
            state.isFollowing = false;
            state.followId = 0;
            state.followerCount -= 1;
            store.dispatch(ActionTypes.FOLLOW_LIST);
          })
          .catch((err) => {
            console.error(err);
          });
      } else {
        axios
          .post('api/follows/', { following: targetUserId }, { headers: headers })
          .then((req) => {
            state.isFollowing = true;
            state.followId = req.data.id;
            state.followerCount += 1;
            store.dispatch(ActionTypes.FOLLOW_LIST);
          })
          .catch((err) => {
            console.error(err);
          });
      }
    };

    onMounted(() => {
      getHaikuList();
      getFollowState();
    });

    //戻る（遷移元の画面に戻る。無ければ検索画面に戻る）
    const goBack = () => {
      const from = router.currentRoute.value.query.from;
      if (typeof from === 'string' && from) {
        router.push(from);
      } else {
        router.push('/search');
      }
    };

    return { state, jwt, isNotLoginUser, displayName, getHaikuList, goBack, toggleFollow };
  },
});
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Yuji+Syuku&family=Shippori+Mincho:wght@500;700&display=swap');

.user-haiku {
  position: relative;
  min-height: calc(100vh - 150px);
  padding: 0 24px 60px;
  background: linear-gradient(180deg, #fbf8f0 0%, #f3ecd9 100%);
  font-family: 'Shippori Mincho', serif;
  color: #2b2621;
}

.user-haiku .back-link {
  display: inline-block;
  margin: 24px 0 0 4px;
  font-size: 13px;
  letter-spacing: 2px;
  color: #6b3b2e;
  cursor: pointer;
  border-bottom: 1px solid #b7a06a;
}

.user-haiku .back-link:hover {
  color: #9c2f24;
  border-bottom-color: #9c2f24;
}

.user-haiku-header {
  max-width: 900px;
  margin: 0 auto 28px;
  padding: 18px 4px 18px;
  border-bottom: 1px solid #d8c9a3;
}

.user-haiku-title {
  font-family: 'Yuji Syuku', serif;
  font-size: 24px;
  letter-spacing: 6px;
  color: #6b3b2e;
  margin: 0;
}

.cards {
  max-width: 900px;
  margin: 0 auto;
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
}

.empty-state {
  max-width: 360px;
  margin: 60px auto 0;
  text-align: center;
  color: #8a7c62;
  font-size: 14px;
  line-height: 2;
}

.follow-area {
  margin-top: 10px;
  display: flex;
  align-items: center;
  gap: 16px;
}

.follower-count {
  font-size: 13px;
  letter-spacing: 1px;
  color: #6b5d45;
}

.follow-button {
  padding: 7px 20px;
  font-family: 'Yuji Syuku', serif;
  font-size: 13px;
  letter-spacing: 2px;
  color: #fbe9e4;
  background: linear-gradient(180deg, #b1453a 0%, #8a271d 100%);
  border: none;
  border-radius: 999px;
  cursor: pointer;
  box-shadow: 0 2px 5px rgba(0, 0, 0, 0.25);
  transition: transform 0.15s ease, box-shadow 0.15s ease, filter 0.15s ease;
}

.follow-button:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.3);
  filter: brightness(1.05);
}

.follow-button.following {
  color: #6b3b2e;
  background: #efe9dd;
  box-shadow: none;
  border: 1px solid #d8c9a3;
}
</style>
