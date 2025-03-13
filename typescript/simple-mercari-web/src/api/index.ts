const SERVER_URL = import.meta.env.VITE_BACKEND_URL || 'http://127.0.0.1:9000';

export const fetchSearchResults = async (keyword: string) => {
  const response = await fetch(`http://localhost:9000/search?keyword=${encodeURIComponent(keyword)}`);
  if (!response.ok) {
    throw new Error('Failed to fetch search results');
  }
  return response.json();
};

export interface Item {
  id: number;
  name: string;
  category: string;
  image_name: string;
}

export interface ItemListResponse {
  items: Item[];
}

export const fetchItems = async (): Promise<ItemListResponse> => {
  const response = await fetch(`${SERVER_URL}/items`, {
    method: 'GET',
    mode: 'cors',
    headers: {
      'Content-Type': 'application/json',
      Accept: 'application/json',
    },
  });
  return response.json();
};

export interface CreateItemInput {
  name: string;
  category: string;
  image: string | File;
}

export const postItem = async (input: CreateItemInput): Promise<Response> => {
  const data = new FormData();
  data.append('name', input.name);
  data.append('category', input.category);
  data.append('image', input.image);
  const response = await fetch(`${SERVER_URL}/items`, {
    method: 'POST',
    mode: 'cors',
    body: data,
  });
  return response;
};
