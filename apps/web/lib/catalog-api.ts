import { api } from "./api";
import type {
  Attribute,
  AttributeValue,
  Brand,
  Category,
  CategoryNode,
  ExchangeRate,
  Product,
  ProductImage,
  ProductList,
  ProductOfferInfo,
  SerialUnit,
} from "./types";

export async function fetchProducts(params: {
  search?: string;
  category_id?: string;
  brand_id?: string;
  active?: boolean;
  published?: boolean;
  admin?: boolean;
  page?: number;
  per_page?: number;
}): Promise<ProductList> {
  const { data } = await api.get<ProductList>("/products", { params });
  return data;
}

export async function fetchProduct(id: string): Promise<Product> {
  const { data } = await api.get<Product>(`/products/${id}`);
  return data;
}

export async function fetchProductBySku(sku: string): Promise<Product> {
  const { data } = await api.get<Product>(`/products/sku/${sku}`);
  return data;
}

export interface ProductCreatePayload {
  name: string;
  barcode?: string | null;
  description?: string | null;
  short_description?: string | null;
  brand_id?: string | null;
  category_id?: string | null;
  cost_price: string;
  sale_price: string;
  currency: string;
  price_rule: string;
  published?: boolean;
  stock_minimum?: number;
  is_serialized?: boolean;
  weight_kg?: string | null;
  notes?: string | null;
  attribute_links?: {
    attribute: string;
    value: string;
    data_type?: string;
    unit?: string | null;
  }[];
}

export async function createProduct(
  payload: ProductCreatePayload
): Promise<Product> {
  const { data } = await api.post<Product>("/products", payload);
  return data;
}

export async function updateProduct(
  id: string,
  payload: Partial<ProductCreatePayload>
): Promise<Product> {
  const { data } = await api.put<Product>(`/products/${id}`, payload);
  return data;
}

export async function deactivateProduct(id: string): Promise<Product> {
  const { data } = await api.delete<Product>(`/products/${id}`);
  return data;
}

export async function publishProduct(id: string): Promise<Product> {
  const { data } = await api.post<Product>(`/products/${id}/publish`);
  return data;
}

export async function unpublishProduct(id: string): Promise<Product> {
  const { data } = await api.post<Product>(`/products/${id}/unpublish`);
  return data;
}

export async function assignAttributes(
  id: string,
  attributes: { attribute: string; value: string }[]
): Promise<Product> {
  const { data } = await api.post<Product>(`/products/${id}/attributes`, {
    attributes,
  });
  return data;
}

export async function registerSerial(
  productId: string,
  payload: {
    serial_number: string;
    imei?: string | null;
    imei2?: string | null;
    mac_address?: string | null;
    status: string;
    notes?: string | null;
  }
): Promise<SerialUnit> {
  const { data } = await api.post<SerialUnit>(
    `/products/${productId}/serials`,
    payload
  );
  return data;
}

export async function fetchBrands(): Promise<Brand[]> {
  const { data } = await api.get<Brand[]>("/brands");
  return data;
}

export async function createBrand(payload: {
  name: string;
}): Promise<Brand> {
  const { data } = await api.post<Brand>("/brands", payload);
  return data;
}

export async function deactivateBrand(id: string): Promise<Brand> {
  const { data } = await api.delete<Brand>(`/brands/${id}`);
  return data;
}

export async function fetchCategories(): Promise<CategoryNode[]> {
  const { data } = await api.get<CategoryNode[]>("/categories");
  return data;
}

export async function fetchCategoriesFlat(): Promise<Category[]> {
  const { data } = await api.get<Category[]>("/categories/flat");
  return data;
}

export async function createCategory(payload: {
  name: string;
  parent_id?: string | null;
  description?: string | null;
}): Promise<Category> {
  const { data } = await api.post<Category>("/categories", payload);
  return data;
}

export async function deactivateCategory(id: string): Promise<Category> {
  const { data } = await api.delete<Category>(`/categories/${id}`);
  return data;
}

export async function fetchAttributes(): Promise<Attribute[]> {
  const { data } = await api.get<Attribute[]>("/attributes");
  return data;
}

export async function createAttribute(payload: {
  name: string;
  data_type: string;
  unit?: string | null;
}): Promise<Attribute> {
  const { data } = await api.post<Attribute>("/attributes", payload);
  return data;
}

export async function fetchAttributeValues(
  attributeId: string
): Promise<AttributeValue[]> {
  const { data } = await api.get<AttributeValue[]>(
    `/attributes/${attributeId}/values`
  );
  return data;
}

export async function addAttributeValue(
  attributeId: string,
  value: string
): Promise<AttributeValue> {
  const { data } = await api.post<AttributeValue>(
    `/attributes/${attributeId}/values`,
    { value }
  );
  return data;
}

export async function fetchCurrentExchangeRate(): Promise<ExchangeRate> {
  const { data } = await api.get<ExchangeRate>(
    "/exchange-rates/current?from=USD&to=PEN"
  );
  return data;
}

export async function uploadFile(file: File): Promise<{
  id: string;
  original_name: string;
  mime_type: string;
  size: number;
  checksum: string;
}> {
  const formData = new FormData();
  formData.append("file", file);
  const { data } = await api.post("/files/upload", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data;
}

export async function attachImage(
  productId: string,
  fileId: string
): Promise<ProductImage> {
  const { data } = await api.post<ProductImage>(
    `/products/${productId}/images?file_id=${fileId}`
  );
  return data;
}

export async function createOffer(
  productId: string,
  payload: {
    normal_price: string;
    offer_price: string;
    start_at: string;
    end_at: string;
  }
): Promise<ProductOfferInfo> {
  const { data } = await api.post<ProductOfferInfo>(
    `/products/${productId}/offers`,
    payload
  );
  return data;
}

export type { SerialUnit, ProductImage, ProductOfferInfo };