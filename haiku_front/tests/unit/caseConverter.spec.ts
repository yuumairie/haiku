import { describe, expect, it } from 'vitest';
import { toCamelCase, toSnakeCase } from '@/utils/caseConverter';

describe('toCamelCase', () => {
  it('snake_caseのキーをcamelCaseに変換する(正常系)', () => {
    const input = { is_public: true, created_at: '2026-01-01', user_post: 1 };
    expect(toCamelCase(input)).toEqual({
      isPublic: true,
      createdAt: '2026-01-01',
      userPost: 1,
    });
  });

  it('配列やネストしたオブジェクトも再帰的に変換する(正常系)', () => {
    const input = [{ good_list: [{ user_id: 1, created_at: 'x' }] }];
    expect(toCamelCase(input)).toEqual([{ goodList: [{ userId: 1, createdAt: 'x' }] }]);
  });

  it('既にcamelCaseのキーは変化しない(異常系・冪等性)', () => {
    const input = { alreadyCamel: 1 };
    expect(toCamelCase(input)).toEqual({ alreadyCamel: 1 });
  });

  it('null/undefined/プリミティブ値はそのまま返す(異常系)', () => {
    expect(toCamelCase(null)).toBeNull();
    expect(toCamelCase(undefined)).toBeUndefined();
    expect(toCamelCase('plain string')).toBe('plain string');
    expect(toCamelCase(42)).toBe(42);
  });

  it('FormDataなどのプレーンオブジェクトでない値は変換せずそのまま返す(異常系)', () => {
    const formData = new FormData();
    formData.append('avatar', 'dummy');
    expect(toCamelCase(formData)).toBe(formData);
  });
});

describe('toSnakeCase', () => {
  it('camelCaseのキーをsnake_caseに変換する(正常系)', () => {
    const input = { isPublic: true, createdAt: '2026-01-01', userPost: 1 };
    expect(toSnakeCase(input)).toEqual({
      is_public: true,
      created_at: '2026-01-01',
      user_post: 1,
    });
  });

  it('配列やネストしたオブジェクトも再帰的に変換する(正常系)', () => {
    const input = [{ goodList: [{ userId: 1, createdAt: 'x' }] }];
    expect(toSnakeCase(input)).toEqual([{ good_list: [{ user_id: 1, created_at: 'x' }] }]);
  });

  it('既にsnake_caseのキーは変化しない(異常系・冪等性)', () => {
    const input = { already_snake: 1 };
    expect(toSnakeCase(input)).toEqual({ already_snake: 1 });
  });

  it('toCamelCaseとtoSnakeCaseは互いに逆の変換になる(正常系)', () => {
    const original = { is_public: false, kigo: '桜', season: '春' };
    expect(toSnakeCase(toCamelCase(original))).toEqual(original);
  });
});
