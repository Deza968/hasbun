import type { Category } from "@/lib/types";

export function flattenCategories(
  categories: Category[],
  depth = 0,
  acc: { category: Category; depth: number }[] = []
): { category: Category; depth: number }[] {
  for (const category of categories) {
    acc.push({ category, depth });
    if (category.children?.length) {
      flattenCategories(category.children, depth + 1, acc);
    }
  }
  return acc;
}

export function formatPrice(value: string | number): string {
  const number = typeof value === "number" ? value : Number(value);
  return `S/ ${number.toFixed(2)}`;
}