import { useEffect, useState } from 'react';
import { Item, fetchItems } from '~/api';

interface Prop {
  reload: boolean; // add reload property
  onLoadCompleted: () => void; // add onLoadCompleted proparty
  searchQuery: string; // add searchQuery property
}

export const ItemList = ({ reload, onLoadCompleted, searchQuery }: Prop) => {
  const [items, setItems] = useState<Item[]>([]);

  useEffect(() => {
    const fetchData = () => {
      fetchItems()
        .then((data) => {
          console.debug('GET success:', data);
          setItems(data.items);
          onLoadCompleted();
        })
        .catch((error) => {
          console.error('GET error:', error);
        });
    };

    if (reload) {
      fetchData();
    }
  }, [reload, onLoadCompleted]);

  // filtering items based on search query
  const filteredItems = items.filter((item) =>
    item.name.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="ItemList">
      {filteredItems.map((item) => (
        <div key={item.id}>
          <img 
            src={`http://localhost:9000/image/${item.image_name}`} 
            alt={item.name} 
            className="ItemImage"
          />
          <p className="ItemDetails">
            <span>Name: {item.name}</span>
            <br />
            <span>Category: {item.category}</span>
          </p>
        </div>
      ))}
    </div>
  );
};