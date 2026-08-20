export interface User {
  id: string;
  email: string;
  username: string;
  full_name: string;
  phone: string | null;
  is_active: boolean;
  is_superuser: boolean;
  last_login_at: string | null;
  created_at: string;
  roles: string[];
  permissions?: string[];
}

export interface UserList {
  items: User[];
  total: number;
}

export interface Role {
  id: string;
  code: string;
  name: string;
  description: string | null;
  is_system: boolean;
  created_at: string;
  permissions: string[];
}

export interface Permission {
  id: string;
  code: string;
  module: string;
  description: string | null;
}

export interface AuditLog {
  id: string;
  action: string;
  module: string;
  user_email: string | null;
  entity_type: string | null;
  entity_id: string | null;
  old_values: Record<string, unknown> | null;
  new_values: Record<string, unknown> | null;
  created_at: string;
}

export interface AuditList {
  items: AuditLog[];
  total: number;
}

export interface Brand {
  id: string;
  name: string;
  slug: string;
  logo_file_id: string | null;
  active: boolean;
  created_at: string;
}

export interface CategoryNode {
  id: string;
  name: string;
  slug: string;
  parent_id: string | null;
  description: string | null;
  active: boolean;
  children: CategoryNode[];
}

export interface Category {
  id: string;
  name: string;
  slug: string;
  parent_id: string | null;
  description: string | null;
  active: boolean;
  created_at: string;
}

export interface Attribute {
  id: string;
  name: string;
  data_type: string;
  unit: string | null;
  created_at: string;
}

export interface AttributeValue {
  id: string;
  attribute_id: string;
  value: string;
}

export interface AttributeLink {
  attribute: string;
  data_type: string;
  unit: string | null;
  value: string;
}

export interface SerialUnit {
  id: string;
  serial_number: string;
  imei: string | null;
  imei2: string | null;
  mac_address: string | null;
  status: string;
  notes: string | null;
  created_at: string;
}

export interface ProductOfferInfo {
  id: string;
  normal_price: string;
  offer_price: string;
  start_at: string;
  end_at: string;
  active: boolean;
  created_at: string;
}

export interface ProductImage {
  id: string;
  file_id: string;
  display_order: number;
  is_primary: boolean;
  url: string | null;
}

export interface Product {
  id: string;
  sku: string;
  barcode: string | null;
  name: string;
  slug: string;
  description: string | null;
  short_description: string | null;
  brand_id: string | null;
  brand_name: string | null;
  category_id: string | null;
  category_name: string | null;
  cost_price: string;
  sale_price: string;
  currency: string;
  price_rule: string;
  active: boolean;
  published: boolean;
  stock_minimum: number;
  is_serialized: boolean;
  weight_kg: string | null;
  notes: string | null;
  created_at: string;
  updated_at: string;
  attributes: AttributeLink[];
  serials: SerialUnit[];
  offers: ProductOfferInfo[];
  images: ProductImage[];
  current_price: string | null;
  current_currency: string | null;
}

export interface ProductList {
  items: Product[];
  total: number;
}

export interface ExchangeRate {
  id: string;
  currency_from: string;
  currency_to: string;
  rate: string;
  source: string;
  effective_at: string;
  created_at: string;
}