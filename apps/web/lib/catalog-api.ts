import { api } from "./api";
import type {
  Attribute,
  Brand,
  BrandCreate,
  Category,
  CategoryCreate,
  Product,
  ProductList,
  PublicProduct,
  PublicProductList,
  SerializedUnit,
} from "./types";

// ---------- Marcas ----------

export async function fetchBrands(): Promise<Brand[]> {
  const { data } = await api.get<Brand[]>("/brands");
  return data;
}

export async function createBrand(payload: BrandCreate): Promise<Brand> {
  const { data } = await api.post<Brand>("/brands", payload);
  return data;
}

// ---------- Categorías ----------

export async function fetchCategories(): Promise<Category[]> {
  const { data } = await api.get<Category[]>("/categories");
  return data;
}

export async function createCategory(
  payload: CategoryCreate
): Promise<Category> {
  const { data } = await api.post<Category>("/categories", payload);
  return data;
}

export async function deleteCategory(categoryId: string): Promise<void> {
  await api.delete(`/categories/${categoryId}`);
}

// ---------- Atributos ----------

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

export async function addAttributeValue(
  attributeId: string,
  value: string
): Promise<void> {
  await api.post(`/attributes/${attributeId}/values`, { value });
}

// ---------- Productos (admin) ----------

export interface ProductListParams {
  offset?: number;
  limit?: number;
  search?: string;
  category_id?: string;
  brand_id?: string;
  active?: boolean;
  published?: boolean;
}

export async function fetchProducts(
  params: ProductListParams = {}
): Promise<ProductList> {
  const { data } = await api.get<ProductList>("/products/admin", { params });
  return data;
}

export async function fetchProduct(productId: string): Promise<Product> {
  const { data } = await api.get<Product>(`/products/admin/${productId}`);
  return data;
}

export async function createProduct(payload: Record<string, unknown>): Promise<Product> {
  const { data } = await api.post<Product>("/products", payload);
  return data;
}

export async function updateProduct(
  productId: string,
  payload: Record<string, unknown>
): Promise<Product> {
  const { data } = await api.put<Product>(`/products/${productId}`, payload);
  return data;
}

export async function publishProduct(productId: string): Promise<Product> {
  const { data } = await api.post<Product>(`/products/${productId}/publish`);
  return data;
}

export async function unpublishProduct(productId: string): Promise<Product> {
  const { data } = await api.post<Product>(`/products/${productId}/unpublish`);
  return data;
}

export async function deactivateProduct(productId: string): Promise<void> {
  await api.delete(`/products/${productId}`);
}

export async function setProductAttributes(
  productId: string,
  attributes: { attribute_id: string; value: string }[]
): Promise<Product> {
  const { data } = await api.post<Product>(
    `/products/${productId}/attributes`,
    attributes
  );
  return data;
}

// ---------- Seriales ----------

export async function fetchSerials(productId: string): Promise<SerializedUnit[]> {
  const { data } = await api.get<SerializedUnit[]>(
    `/products/${productId}/serials`
  );
  return data;
}

export async function registerSerial(
  productId: string,
  payload: {
    serial_number: string;
    imei?: string | null;
    imei2?: string | null;
    mac_address?: string | null;
    notes?: string | null;
  }
): Promise<SerializedUnit> {
  const { data } = await api.post<SerializedUnit>(
    `/products/${productId}/serials`,
    payload
  );
  return data;
}

export async function updateSerialStatus(
  productId: string,
  serialId: string,
  status: string,
  notes?: string | null
): Promise<SerializedUnit> {
  const { data } = await api.put<SerializedUnit>(
    `/products/${productId}/serials/${serialId}`,
    { status, notes }
  );
  return data;
}

// ---------- Ofertas ----------

export async function fetchOffers(productId: string): Promise<
  {
    id: string;
    normal_price: string;
    offer_price: string;
    start_at: string;
    end_at: string;
    active: boolean;
  }[]
> {
  const { data } = await api.get(`/products/${productId}/offers`);
  return data;
}

export async function createOffer(
  productId: string,
  payload: {
    normal_price: number;
    offer_price: number;
    start_at: string;
    end_at: string;
  }
): Promise<unknown> {
  const { data } = await api.post(`/products/${productId}/offers`, payload);
  return data;
}

export async function deactivateOffer(
  productId: string,
  offerId: string
): Promise<void> {
  await api.delete(`/products/${productId}/offers/${offerId}`);
}

// ---------- Archivos ----------

export async function uploadImage(file: File): Promise<{ id: string }> {
  const form = new FormData();
  form.append("file", file);
  const { data } = await api.post<{ id: string }>("/files/upload", form, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data;
}

export async function addProductImage(
  productId: string,
  file: File
): Promise<unknown> {
  const form = new FormData();
  form.append("file", file);
  const { data } = await api.post(
    `/products/${productId}/images`,
    form,
    { headers: { "Content-Type": "multipart/form-data" } }
  );
  return data;
}

export async function removeProductImage(
  productId: string,
  imageId: string
): Promise<void> {
  await api.delete(`/products/${productId}/images/${imageId}`);
}

export async function setPrimaryImage(
  productId: string,
  imageId: string
): Promise<void> {
  await api.post(`/products/${productId}/images/${imageId}/primary`);
}

// ---------- Tienda pública ----------

export interface PublicProductParams {
  offset?: number;
  limit?: number;
  search?: string;
  category_id?: string;
  brand_id?: string;
}

export async function fetchPublicProducts(
  params: PublicProductParams = {}
): Promise<PublicProductList> {
  const { data } = await api.get<PublicProductList>("/products", { params });
  return data;
}

export async function fetchPublicProductBySlug(
  slug: string
): Promise<PublicProduct> {
  const { data } = await api.get<PublicProduct>(`/products/slug/${slug}`);
  return data;
}