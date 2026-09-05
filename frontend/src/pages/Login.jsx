import React, { useState } from 'react';
import { Link } from "react-router-dom";

import { useNavigate, useLocation } from "react-router-dom";
import { useUser } from "../context/UserContext";
import { apiFetch } from "@/services/api";


const Login = () => {
  const [form, setForm] = useState({ email: '', password: '' });
  const [message, setMessage] = useState('');
  const [error, setError] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();
  const { login } = useUser();

  // Capture redirect path (e.g., from /login?redirect=/join-league/abc123)
  const redirectPath = new URLSearchParams(location.search).get("redirect") || "/";

  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  const handleLogin = async (e) => {
    e.preventDefault();
    setMessage('');
    setError(false);

    const { email, password } = form;
    if (!email || !password) {
      setMessage("🚫 Email and password required.");
      setError(true);
      return;
    }

    try {
      const response = await apiFetch('/api/users/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(form),
      });

      const data = await response.json();

      if (response.ok) {
        if (!data?.user) throw new Error("Missing user data from backend");

        login(data);
        localStorage.setItem("token", data.token);

        setMessage("✅ Login successful! Redirecting...");

        // Check if there is a pending invite token in localStorage
        const pendingInviteToken = localStorage.getItem("pending_invite_token");
        if (pendingInviteToken) {
          localStorage.removeItem("pending_invite_token");
          setTimeout(() => navigate(`/join-league/${pendingInviteToken}`), 1000);
        } else {
          setTimeout(() => navigate(redirectPath), 1000); // Normal redirect if no pending invite
        }
      } else {
        setError(true);
        setMessage(data.detail || "🚫 Login failed.");
      }
    } catch (err) {
      console.error("Login error:", err);
      setMessage("🚫 Network error. Try again.");
      setError(true);
    }
  };

  return (
    <div className="max-w-sm mx-auto mt-8">
      <h2 className="text-2xl font-semibold mb-4">Log In</h2>
      <form onSubmit={handleLogin}>
        <input
          className="w-full p-2 border mb-4 rounded"
          placeholder="Email"
          name="email"
          type="email"
          autoComplete="off"
          value={form.email}
          onChange={handleChange}
        />
        <input
          className="w-full p-2 border mb-4 rounded"
          placeholder="Password"
          name="password"
          type="password"
          autoComplete="off"
          value={form.password}
          onChange={handleChange}
        />
        <button
          type="submit"
          className="w-full bg-blue-600 text-white py-2 rounded hover:bg-blue-700"
        >
          Log In
        </button>
        <p className="mt-4 text-center">
          <Link to="/forgot-password" className="text-blue-600 hover:underline">
            Forgot Password?
          </Link>
        </p>
      </form>
      {message && (
        <p className={`mt-4 text-center text-sm ${error ? 'text-red-600' : 'text-green-600'}`}>
          {message}
        </p>
      )}
    </div>
  );
};

export default Login;
