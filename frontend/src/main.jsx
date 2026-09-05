import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import App from './App';
import { UserProvider } from './context/UserContext';
import { SeasonProvider } from "@/context/SeasonContext";
import { LeagueProvider } from "@/context/LeagueContext";

import './index.css'; // Optional styling import

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <BrowserRouter>
      <LeagueProvider>
        <SeasonProvider>
          <UserProvider>
            <App />
          </UserProvider>
        </SeasonProvider>
      </LeagueProvider>
    </BrowserRouter>
  </React.StrictMode>
);
