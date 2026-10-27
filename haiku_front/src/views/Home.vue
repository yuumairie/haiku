<template>
  <div class="home">
    <div class="home-header">
      <h2 class="home-title">皆の句</h2>
      <div class="header-links">
        <router-link to="/search" class="mine-link">検索</router-link>
        <template v-if="jwt">
          <router-link to="/mine" class="mine-link">我が句</router-link>
          <router-link to="/post" class="post-button">句を投函する</router-link>
        </template>
      </div>
    </div>

    <div v-if="jwt" class="tabs">
      <div
        class="tab"
        :class="{ active: activeTab === 'new' }"
        @click="activeTab = 'new'"
      >
        新着
      </div>
      <div
        class="tab"
        :class="{ active: activeTab === 'following' }"
        @click="activeTab = 'following'"
      >
        購読中
      </div>
      <div
        class="tab"
        :class="{ active: activeTab === 'liked' }"
        @click="activeTab = 'liked'"
      >
        ゆかしき句
      </div>
    </div>

    <div v-if="displayedHaikuList.length" class="cards">
      <div v-for="haiku in displayedHaikuList" :key="haiku.id">
        <Haiku-Card
          :haiku="haiku"
          :isNotLoginUser="isNotLoginUser(haiku.userPost.id)"
          list-from="home"
          @get-haiku-list="getHaikuList"
        />
      </div>
    </div>
    <div v-else-if="activeTab === 'following'" class="empty-state">
      まだ購読中の歌人の句がありません。
    </div>
    <div v-else-if="activeTab === 'liked'" class="empty-state">
      まだゆかしき句がありません。
    </div>
    <div v-else class="empty-state">
      まだ他の人の句が投稿されていません。
      <br v-if="jwt" />
      <span v-if="jwt">最初の一句を詠んでみませんか。</span>
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent, onMounted, reactive, computed } from 'vue';
import axios from 'axios';
import HaikuCard from '../components/HaikuCard.vue';
import { MutationTypes, useStore } from '../store';
import { HaikuModel, FollowModel, GoodModel } from '../types/task';
export default defineComponent({
  name: 'home',
  components: {
    HaikuCard,
  },
  setup() {
    const store = useStore();
    const state = reactive({
      haikuList: [] as HaikuModel[],
    });

    // 選択中のタブ。戻るボタンで画面に戻った時にも選択していたタブを
    // 復元できるよう、コンポーネントのローカル状態ではなくストアで持つ
    const activeTab = computed({
      get: () => store.getters.getHomeTab,
      set: (value: 'new' | 'following' | 'liked') => {
        store.commit(MutationTypes.SET_HOME_TAB, value);
      },
    });
    const jwt = computed(() => {
      return store.getters.getToken;
    });

    //自分の投稿を除いた一覧（ホームは「他の人の俳句」を表示する画面にする）
    const otherHaikuList = computed(() => {
      if (!jwt.value) {
        return state.haikuList;
      }
      return state.haikuList.filter((haiku) => haiku.userPost.id !== store.getters.getUserId);
    });

    //自分がフォローしているユーザのIDの一覧
    const followingIds = computed<Array<number>>(() => {
      return (store.getters.getFollowList as Array<FollowModel>).map(
        (follow) => follow.following.id
      );
    });

    //「新着」のうち、フォロー中のユーザの句だけに絞り込んだもの
    const followingHaikuList = computed(() => {
      return otherHaikuList.value.filter((haiku) => followingIds.value.includes(haiku.userPost.id));
    });

    //自分がいいね（をかし）した句のIDの一覧
    const likedHaikuIds = computed<Array<number>>(() => {
      return (store.getters.getGoodList as Array<GoodModel>)
        .filter((good) => good.user === store.getters.getUserId)
        .map((good) => Number(good.haiku));
    });

    //自分がいいねした句の一覧
    const likedHaikuList = computed(() => {
      return state.haikuList.filter((haiku) => likedHaikuIds.value.includes(haiku.id));
    });

    //選択中のタブに応じて表示する一覧を切り替える
    const displayedHaikuList = computed(() => {
      if (jwt.value && activeTab.value === 'following') {
        return followingHaikuList.value;
      }
      if (jwt.value && activeTab.value === 'liked') {
        return likedHaikuList.value;
      }
      return otherHaikuList.value;
    });

    const getHaikuList = (): void => {
      axios
        .get('/api/haikus/')
        .then((req) => {
          state.haikuList = req.data;
        })
        .catch((err) => {
          console.error(err);
        });
    };

    onMounted(() => {
      getHaikuList();
    });
    const isNotLoginUser = (id: number): boolean => {
      if (jwt.value) {
        return store.getters.getUserId !== id;
      }
      return false;
    };

    return {
      state,
      jwt,
      activeTab,
      otherHaikuList,
      followingHaikuList,
      likedHaikuList,
      displayedHaikuList,
      isNotLoginUser,
      getHaikuList,
    };
  },
});
</script>
<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Yuji+Syuku&family=Shippori+Mincho:wght@500;700&display=swap');

.home {
  min-height: calc(100vh - 150px);
  padding: 0 24px 60px;
  background: linear-gradient(180deg, #fbf8f0 0%, #f3ecd9 100%);
  font-family: 'Shippori Mincho', serif;
  color: #2b2621;
}

.home-header {
  max-width: 900px;
  margin: 0 auto 28px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 28px 4px 18px;
  border-bottom: 1px solid #d8c9a3;
}

.home-title {
  font-family: 'Yuji Syuku', serif;
  font-size: 26px;
  letter-spacing: 8px;
  color: #6b3b2e;
  margin: 0;
}

.header-links {
  display: flex;
  align-items: center;
  gap: 12px;
}

.mine-link {
  font-size: 13px;
  letter-spacing: 2px;
  color: #6b3b2e;
  text-decoration: none;
  border-bottom: 1px solid #b7a06a;
  white-space: nowrap;
}

.mine-link:hover {
  color: #9c2f24;
  border-bottom-color: #9c2f24;
}

.post-button {
  display: inline-block;
  padding: 9px 22px;
  font-family: 'Yuji Syuku', serif;
  font-size: 14px;
  letter-spacing: 3px;
  color: #fbe9e4;
  background: linear-gradient(180deg, #b1453a 0%, #8a271d 100%);
  border-radius: 999px;
  text-decoration: none;
  white-space: nowrap;
  box-shadow: 0 2px 5px rgba(0, 0, 0, 0.25);
  transition: transform 0.15s ease, box-shadow 0.15s ease, filter 0.15s ease;
}

.post-button:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.3);
  filter: brightness(1.05);
}

.tabs {
  max-width: 900px;
  margin: 0 auto 20px;
  display: flex;
  gap: 8px;
}

.tab {
  padding: 7px 18px;
  font-size: 13px;
  letter-spacing: 2px;
  color: #8a7c62;
  background: #efe9dd;
  border: 1px solid #d8c9a3;
  border-radius: 999px;
  cursor: pointer;
  white-space: nowrap;
}

.tab:hover {
  color: #6b3b2e;
}

.tab.active {
  color: #fbe9e4;
  background: linear-gradient(180deg, #b1453a 0%, #8a271d 100%);
  border-color: transparent;
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
</style>
