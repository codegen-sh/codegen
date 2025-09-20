import React from 'react';
import { Header } from 'Header';
import { Footer } from 'Footer';

const Sidebar: React.FC = () => {
  return <div>Sidebar Content</div>;
};

const MainContent: React.FC = () => {
  return <div>Main Content</div>;
};

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
