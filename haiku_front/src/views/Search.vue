<template>
  <div class="search-page">
    <h2 class="search-title">検索</h2>

    <section class="search-section">
      <h3 class="section-title">俳句を検索</h3>
      <div class="search-form">
        <input
          type="text"
          v-model="state.haikuKeyword"
          class="search-input"
          placeholder="句の内容を入力"
          @keyup.enter="searchHaiku()"
        />
        <select v-model="state.season" class="season-select">
          <option value="">季節：すべて</option>
          <option value="春">春</option>
          <option value="夏">夏</option>
          <option value="秋">秋</option>
          <option value="冬">冬</option>
          <option value="新年">新年</option>
        </select>
        <button class="search-button" @click="searchHaiku()">検索</button>
      </div>

      <div v-if="state.haikuSearched">
        <div v-if="state.haikuResults.length" class="cards">
          <div v-for="haiku in state.haikuResults" :key="haiku.id">
            <Haiku-Card
              :haiku="haiku"
              :isNotLoginUser="isNotLoginUser(haiku.userPost.id)"
              list-from="search"
              @get-haiku-list="searchHaiku"
            />
          </div>
        </div>
        <div v-else class="empty-state">該当する句が見つかりませんでした。</div>
      </div>
    </section>

    <section class="search-section">
      <h3 class="section-title">ユーザを検索</h3>
      <div class="search-form">
        <input
          type="text"
          v-model="state.userKeyword"
          class="search-input"
          placeholder="ユーザ名を入力"
          @keyup.enter="searchUser()"
        />
        <button class="search-button" @click="searchUser()">検索</button>
      </div>

      <div v-if="state.userSearched">
        <div v-if="state.userResults.length" class="user-list">
          <div
            v-for="user in state.userResults"
            :key="user.id"
            class="user-item"
            @click="goToUser(user.id)"
          >
            {{ user.username || '匿名' }}
          </div>
        </div>
        <div v-else class="empty-state">該当するユーザが見つかりませんでした。</div>
      </div>
    </section>
  </div>
</template>

<script lang="ts">
import { defineComponent, reactive, computed } from 'vue';
import axios from 'axios';
import HaikuCard from '../components/HaikuCard.vue';
import { useStore } from '../store';
import { useRouter } from '../router';
import { HaikuModel, UserModel } from '../types/task';

export default defineComponent({
  name: 'search',
  components: {
    HaikuCard,
  },
  setup() {
    const store = useStore();
    const router = useRouter();

    const state = reactive({
      haikuKeyword: '',
      season: '',
      haikuResults: [] as HaikuModel[],
      haikuSearched: false,
      userKeyword: '',
      userResults: [] as UserModel[],
      userSearched: false,
    });

    const jwt = computed(() => {
      return store.getters.getToken;
    });

    const isNotLoginUser = (id: number): boolean => {
      if (jwt.value) {
        return store.getters.getUserId !== id;
      }
      return false;
    };

    //俳句をキーワードで検索する
    const searchHaiku = (): void => {
      axios
        .get('/api/haikus/', {
          params: { content: state.haikuKeyword, season: state.season },
        })
        .then((req) => {
          state.haikuResults = req.data;
          state.haikuSearched = true;
        })
        .catch((err) => {
          console.error(err);
        });
    };

    //ユーザ名でユーザを検索する
    const searchUser = (): void => {
      axios
        .get('/api/users/', { params: { username: state.userKeyword } })
        .then((req) => {
          state.userResults = req.data;
          state.userSearched = true;
        })
        .catch((err) => {
          console.error(err);
        });
    };

    //検索結果のユーザの句一覧画面へ遷移する
    const goToUser = (id: number): void => {
      router.push({
        path: `/user/${id}`,
        query: { from: router.currentRoute.value.fullPath },
      });
    };

    return { state, searchHaiku, searchUser, isNotLoginUser, goToUser };
  },
});
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Yuji+Syuku&family=Shippori+Mincho:wght@500;700&display=swap');

.search-page {
  min-height: calc(100vh - 150px);
  padding: 0 24px 60px;
  background: linear-gradient(180deg, #fbf8f0 0%, #f3ecd9 100%);
  font-family: 'Shippori Mincho', serif;
  color: #2b2621;
}

.search-title {
  max-width: 900px;
  margin: 0 auto;
  padding: 28px 4px 18px;
  font-family: 'Yuji Syuku', serif;
  font-size: 26px;
  letter-spacing: 8px;
  color: #6b3b2e;
  border-bottom: 1px solid #d8c9a3;
}

.search-section {
  max-width: 900px;
  margin: 0 auto 36px;
  padding-top: 24px;
}

.section-title {
  font-size: 16px;
  letter-spacing: 3px;
  color: #6b3b2e;
  margin: 0 0 14px;
}

.search-form {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.search-input {
  flex: 1;
  min-width: 200px;
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

.search-input::placeholder {
  color: #b7a888;
}

.season-select {
  padding: 10px 12px;
  border: 1px solid #d8c9a3;
  border-radius: 2px;
  background: #fffdf6;
  font-family: 'Shippori Mincho', serif;
  font-size: 15px;
  color: #2b2621;
  outline: none;
}

.search-button {
  padding: 10px 24px;
  font-family: 'Yuji Syuku', serif;
  font-size: 14px;
  letter-spacing: 3px;
  color: #fbe9e4;
  background: linear-gradient(180deg, #b1453a 0%, #8a271d 100%);
  border: none;
  border-radius: 999px;
  cursor: pointer;
  box-shadow: 0 2px 5px rgba(0, 0, 0, 0.25);
  transition: transform 0.15s ease, box-shadow 0.15s ease, filter 0.15s ease;
}

.search-button:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.3);
  filter: brightness(1.05);
}

.cards {
  margin-top: 24px;
  display: flex;
  flex-wrap: wrap;
}

.user-list {
  margin-top: 20px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  max-width: 420px;
}

.user-item {
  padding: 12px 16px;
  background-color: #fffdf6;
  border: 1px solid #e3d9bd;
  border-radius: 2px;
  font-size: 15px;
  letter-spacing: 1px;
  cursor: pointer;
  transition: border-color 0.15s ease, color 0.15s ease;
}

.user-item:hover {
  color: #9c2f24;
  border-color: #9c2f24;
}

.empty-state {
  margin-top: 24px;
  color: #8a7c62;
  font-size: 14px;
  line-height: 2;
}
</style>
