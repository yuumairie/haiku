<template>
  <div class="my-haiku">
    <div class="my-haiku-header">
      <h2 class="my-haiku-title">我が句</h2>
      <div class="header-links">
        <router-link to="/home" class="home-link">皆の句</router-link>
        <router-link to="/search" class="home-link">検索</router-link>
        <router-link to="/post" class="post-button">句を投函する</router-link>
      </div>
    </div>

    <div v-if="state.haikuList.length" class="cards">
      <div v-for="haiku in state.haikuList" :key="haiku.id">
        <Haiku-Card
          :haiku="haiku"
          :isNotLoginUser="false"
          list-from="mine"
          @get-haiku-list="getHaikuList"
        />
      </div>
    </div>
    <div v-else class="empty-state">
      まだあなたの句が投稿されていません。
      <br />
      <span>最初の一句を詠んでみませんか。</span>
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent, reactive, computed, watch } from 'vue';
import axios from 'axios';
import HaikuCard from '../components/HaikuCard.vue';
import { useStore } from '../store';
import { HaikuModel } from '../types/task';
export default defineComponent({
  name: 'my-haiku',
  components: {
    HaikuCard,
  },
  setup() {
    const store = useStore();
    const state = reactive({
      haikuList: [] as HaikuModel[],
    });

    const userId = computed(() => store.getters.getUserId);

    //userPostをクエリパラメータに付けて、自分の投稿だけをサーバー側で絞り込んでもらう
    const getHaikuList = (): void => {
      axios
        .get('/api/haikus/', {
          params: { userPost: userId.value },
        })
        .then((req) => {
          state.haikuList = req.data;
        })
        .catch((err) => {
          console.error(err);
        });
    };

    //リロード直後はuserIdの取得が非同期で遅れて届くことがあるため、
    //userIdが確定してから（0以外になってから）取得する
    watch(
      userId,
      (id) => {
        if (id) {
          getHaikuList();
        }
      },
      { immediate: true }
    );

    return { state, getHaikuList };
  },
});
</script>
<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Yuji+Syuku&family=Shippori+Mincho:wght@500;700&display=swap');

.my-haiku {
  min-height: calc(100vh - 150px);
  padding: 0 24px 60px;
  background: linear-gradient(180deg, #fbf8f0 0%, #f3ecd9 100%);
  font-family: 'Shippori Mincho', serif;
  color: #2b2621;
}

.my-haiku-header {
  max-width: 900px;
  margin: 0 auto 28px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 28px 4px 18px;
  border-bottom: 1px solid #d8c9a3;
}

.my-haiku-title {
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

.home-link {
  font-size: 13px;
  letter-spacing: 2px;
  color: #6b3b2e;
  text-decoration: none;
  border-bottom: 1px solid #b7a06a;
  white-space: nowrap;
}

.home-link:hover {
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
