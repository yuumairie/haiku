<template>
  <div class="root">
    <header id="nav">
      <h1 class="nav-bar" @click="goToHome()">
        <img class="header-image" :src="require('@/assets/images/ヘッダ2.png')" />
      </h1>
      <div class="icons">
        <router-link to="/register" v-if="!jwt">
          <div class="icon">
            <img style="height: 20px" :src="require('@/assets/images/登録.png')" />
            新規登録
          </div></router-link
        >
        <router-link to="/login" v-if="!jwt">
          <div class="icon">
            <img style="height: 20px" :src="require('@/assets/images/ログイン.png')" />
            ログイン
          </div></router-link
        >
        <router-link to="/myprofile" v-if="jwt"> <div class="icon">プロフィール</div></router-link>
        <div class="icon logout" v-if="jwt" @click="logout()">ログアウト</div>
      </div>
    </header>
    <div class="content">
      <router-view />
      <div class="footer">Copyright © 2020 Inc. Co., Ltd., All Rights Unreserved.</div>
    </div>
  </div>
</template>
<script lang="ts">
import { computed, defineComponent } from 'vue';
import { useRouter } from '../src/router';
import { MutationTypes, useStore } from './store';

export default defineComponent({
  setup() {
    const store = useStore();
    const router = useRouter();
    const jwt = computed(() => {
      return store.getters.getToken;
    });

    const goToHome = () => {
      router.push('/home');
    };

    //ログアウト
    const logout = () => {
      store.commit(MutationTypes.LOGOUT);
      router.push('/home');
    };

    return { goToHome, logout, jwt };
  },
});
</script>
<style scoped>
#app {
  font-family: Avenir, Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-align: center;
  color: #2c3e50;
}
.header-image {
  width: 100%;
  height: 40px;
  object-fit: cover;
  object-position: center;
  display: block;
}
#app #nav {
  position: fixed;
  background-color: floralwhite;
  color: black;
  text-align: left;
  height: 40px;
  width: 100%;
  margin: 0;
  top: 0;
  left: 0;
  border-bottom: black 2px solid;
  opacity: 0.9;
  z-index: 1030;
  display: flex;
  align-items: center;
}
#nav .btn {
  background-color: white;
  color: black;
}
#nav .nav-bar {
  cursor: pointer;
}
#nav .icon {
  width: 98px;
  margin-right: 15px;
}
#nav .icon.logout {
  cursor: pointer;
}
#nav .icons {
  display: flex;
  margin-left: auto;
}
.content {
  margin-top: 50px;
  display: flex;
  flex-direction: column;
  min-height: calc(100vh - 50px);
}
.footer {
  background-color: aliceblue;
  padding: 7px 0;
  text-align: center;
  margin-top: auto;
}
</style>
