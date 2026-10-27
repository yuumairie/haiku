// snake_case ⇄ camelCase 変換ユーティリティ。
// バックエンド(Django/DRF)はsnake_caseのフィールド名(created_at, is_publicなど)
// を返す/受け取る一方、フロント側はcamelCaseに統一したいため、
// axiosのインターセプタ(main.ts)でこの変換を一括して行う。
// アプリケーション側のコード(各.vueファイル)では、API関連のデータも
// 常にcamelCaseだけを書けばよい。

// 変換対象はプレーンなオブジェクト（{}リテラルやJSONをparseしたもの）だけに
// 限定する。FormData・File・Blob・Date・クラスインスタンス等はキー変換の
// 対象外として、そのまま通す(constructorがObjectと一致するものだけを対象にする)。
const isPlainObject = (value: unknown): value is Record<string, unknown> => {
  return (
    typeof value === 'object' &&
    value !== null &&
    !Array.isArray(value) &&
    value.constructor === Object
  );
};

const snakeToCamelKey = (key: string): string => {
  return key.replace(/_([a-z0-9])/g, (_match, char: string) => char.toUpperCase());
};

const camelToSnakeKey = (key: string): string => {
  return key.replace(/[A-Z]/g, (char) => `_${char.toLowerCase()}`);
};

const deepTransformKeys = (value: unknown, transformKey: (key: string) => string): unknown => {
  if (Array.isArray(value)) {
    return value.map((item) => deepTransformKeys(item, transformKey));
  }
  if (isPlainObject(value)) {
    const result: Record<string, unknown> = {};
    Object.keys(value).forEach((key) => {
      result[transformKey(key)] = deepTransformKeys(value[key], transformKey);
    });
    return result;
  }
  return value;
};

// snake_case → camelCase（APIレスポンスをアプリ側で使う形に変換する）
export const toCamelCase = <T = unknown>(value: unknown): T => {
  return deepTransformKeys(value, snakeToCamelKey) as T;
};

// camelCase → snake_case（アプリ側のデータをAPIに送る形に変換する）
export const toSnakeCase = <T = unknown>(value: unknown): T => {
  return deepTransformKeys(value, camelToSnakeKey) as T;
};
