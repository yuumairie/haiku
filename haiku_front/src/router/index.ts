import { createRouter, createWebHistory, RouteRecordRaw } from 'vue-router';
import Home from '../views/Home.vue';
import RegisterUser from '../views/RegisterUser.vue';
import Login from '../views/Login.vue';
import Post from '../views/Post.vue';
import Detail from '../views/Detail.vue';
import Edit from '../views/Edit.vue';
import MyHaiku from '../views/MyHaiku.vue';
import Comment from '../views/Comment.vue';
import Search from '../views/Search.vue';
import UserHaiku from '../views/UserHaiku.vue';
import MyProfile from '../views/MyProfile.vue';
import { useStore } from '../store';

const routes: Array<RouteRecordRaw> = [
  {
    path: '/home',
    name: 'Home',
    component: Home,
  },
  {
    path: '/register',
    name: 'Register',
    component: RegisterUser,
  },
  {
    path: '/login',
    name: 'Login',
    component: Login,
  },
  {
    path: '/post',
    name: 'Post',
    component: Post,
    beforeEnter: (to, from, next) => {
      if (useStore().getters.getToken) {
        next();
      } else {
        next('login');
      }
    },
  },
  {
    path: '/mine',
    name: 'MyHaiku',
    component: MyHaiku,
    beforeEnter: (to, from, next) => {
      if (useStore().getters.getToken) {
        next();
      } else {
        next('login');
      }
    },
  },
  {
    path: '/detail/:id',
    name: 'Detail',
    component: Detail,
  },
  {
    path: '/edit/:id',
    name: 'Edit',
    component: Edit,
    beforeEnter: (to, from, next) => {
      if (useStore().getters.getToken) {
        next();
      } else {
        next('login');
      }
    },
  },
  {
    path: '/comment/:id',
    name: 'Comment',
    component: Comment,
    beforeEnter: (to, from, next) => {
      if (useStore().getters.getToken) {
        next();
      } else {
        next('login');
      }
    },
  },
  {
    path: '/search',
    name: 'Search',
    component: Search,
  },
  {
    path: '/user/:id',
    name: 'UserHaiku',
    component: UserHaiku,
  },
  {
    path: '/myprofile',
    name: 'MyProfile',
    component: MyProfile,
    beforeEnter: (to, from, next) => {
      if (useStore().getters.getToken) {
        next();
      } else {
        next('login');
      }
    },
  },
];

export const router = createRouter({
  history: createWebHistory(process.env.BASE_URL),
  routes,
});
export const useRouter = () => {
  return router;
};

// export default router
