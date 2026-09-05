import React from 'react';
import { Routes, Route } from 'react-router-dom';
import Home from './pages/Home';
import WeeklyPlayerSelector from './pages/WeeklyPlayerSelector';
import Login from './pages/Login';
import Signup from './pages/Signup';
import Standings from './pages/Standings';
import Rules from './pages/Rules';
import ViewLeagues from './pages/Leagues';
import Layout from './components/Layout';
import CreateLeague from "./pages/CreateLeague";
import LeaguePage from "./pages/LeaguePage";
import JoinLeague from './pages/JoinLeague';
import PlayerStatsPage from './pages/PlayerStatsPage';
import ForgotPassword from './pages/ForgotPassword';
import AdminLeagueFinancePage from "./pages/AdminLeagueFinancePage";
import StreakHistoryPage from "./pages/StreakHistoryPage";

const App = () => (
  <Layout>
    <Routes>
      <Route path="/" element={<Home />} />
      <Route path="/select" element={<WeeklyPlayerSelector />} />
      <Route path="/login" element={<Login />} />
      <Route path="/signup" element={<Signup />} />
      <Route path="/standings" element={<Standings />} />
      <Route path="/rules" element={<Rules />} />
      <Route path="/leagues" element={<ViewLeagues />} />
      <Route path="/create-league" element={<CreateLeague />} />
      <Route path="/leagues/:id" element={<LeaguePage />} />
      <Route path="/join-league/:token" element={<JoinLeague />} />
      <Route path="/playerstats" element={<PlayerStatsPage />} />
      <Route path="/forgot-password" element={<ForgotPassword />} />
      <Route path="/admin/league-finances" element={<AdminLeagueFinancePage />} />
      <Route path="/streak-history" element={<StreakHistoryPage />} />
    </Routes>
  </Layout>
);

export default App;
