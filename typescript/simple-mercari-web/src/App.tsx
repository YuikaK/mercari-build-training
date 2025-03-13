import { useState } from 'react';
import './App.css';
import { ItemList } from '~/components/ItemList';
import { Listing } from '~/components/Listing';

function App() {
  const [reload, setReload] = useState(true);
  const [searchQuery, setSearchQuery] = useState(''); 

  return (
    <div>
      <header className="Title">
        <p>
          <b>Simple Mercari</b>
        </p>
      </header>
      <div>
        <Listing
          onListingCompleted={() => setReload(true)}
          setSearchQuery={setSearchQuery} 
        />
      </div>
      <div>
        <ItemList
          reload={reload}
          onLoadCompleted={() => setReload(false)}
          searchQuery={searchQuery} // searchQuery
        />
      </div>
    </div>
  );
}

export default App;