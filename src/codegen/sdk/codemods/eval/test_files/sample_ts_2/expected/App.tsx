import { Sidebar } from 'Sidebar';
import { MainContent } from  'MainContent';
import React from 'react';
import { Header } from 'Header';
import { Footer } from 'Footer';


export const App: React.FC = () => {
  const userName = "John";
  return (
    <div>
      <Header />
      <Sidebar />
      <MainContent />
      <Footer />
      <p>Welcome, ' + userName + '!</p>
    </div>
  );
};

export default App;
