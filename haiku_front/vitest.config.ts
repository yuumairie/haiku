import { defineConfig } from 'vite';
import vue from '@vitejs/plugin-vue';
import path from 'path';

// フロントエンドのユニットテスト(Vitest + Vue Test Utils)用の設定。
// エイリアス(@ -> src)はtsconfig.json/webpackの設定に合わせている。
export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, 'src'),
    },
  },
  test: {
    environment: 'jsdom',
    globals: true,
    include: ['tests/unit/**/*.spec.ts'],
  },
});
