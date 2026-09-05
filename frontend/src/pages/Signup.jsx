import React, { useState } from 'react';
import { useNavigate } from "react-router-dom";
import { useUser } from "../context/UserContext";
import { apiFetch } from "@/services/api";

const Signup = () => {
  const [form, setForm] = useState({ name: '', email: '', password: '', confirmPassword: '' });
  const [message, setMessage] = useState('');
  const [error, setError] = useState(false);
  const [loading, setLoading] = useState(false);

  const navigate = useNavigate();
  const { login, setActiveLeagueId } = useUser(); // setActiveLeagueId kept if you want to use it elsewhere

  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    await handleSignup();
  };

  const handleSignup = async () => {
    setMessage('');
    setError(false);
    setLoading(true);

    const { name, email, password, confirmPassword } = form;

    if (!name || !email || !password || !confirmPassword) {
      setMessage("🚫 All fields are required.");
      setError(true);
      setLoading(false);
      return;
    }

    if (password !== confirmPassword) {
      setMessage("🚫 Password and Confirm Password do not match.");
      setError(true);
      setLoading(false);
      return;
    }

    try {
      const response = await apiFetch('/api/users/signup', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, email, password }),
      });

      const data = await response.json();

      if (response.ok) {
        if (!data?.token) {
          setMessage("🚫 Signup succeeded but no token received.");
          setError(true);
          setLoading(false);
          return;
        }

        await login(data); // await if login is async

        setMessage("✅ Account created! Redirecting...");
        setError(false);

        const pendingInviteToken = localStorage.getItem("pending_invite_token");

        if (pendingInviteToken) {
          localStorage.removeItem("pending_invite_token");
          setTimeout(() => {
            navigate(`/join-league/${pendingInviteToken}`);
          }, 1200);
        } else {
          setTimeout(() => navigate("/"), 1200);
        }
      } else {
        const detail = data?.detail || "";
        setError(true);
        setMessage(
          response.status === 409 || detail.includes("already")
            ? "🚫 A user with that email already exists."
            : detail || "🚫 Something went wrong."
        );
      }
    } catch (err) {
      console.error("Signup error:", err);

      const isNetworkError =
        err?.message?.includes("Network") ||
        err?.code === "ECONNABORTED" ||
        err?.name === "TypeError"; // fetch throws TypeError on network failure

      if (isNetworkError) {
        setMessage("⏳ Server is waking up. Please try again in 30–90 seconds.");
      } else {
        setMessage("🚫 Network error. Please try again.");
      }

      setError(true);
    } finally {
      setLoading(false);
    }

  };

  return (
    <div className="max-w-sm mx-auto mt-8">
      <h2 className="text-2xl font-semibold mb-4">Sign Up</h2>
      <form onSubmit={handleSubmit}>
        <input
          className="w-full p-2 border mb-4 rounded"
          placeholder="Name"
          name="name"
          value={form.name}
          onChange={handleChange}
          autoComplete="name"
          disabled={loading}
        />
        <input
          className="w-full p-2 border mb-4 rounded"
          placeholder="Email"
          name="email"
          type="email"
          value={form.email}
          onChange={handleChange}
          autoComplete="email"
          disabled={loading}
        />
        <input
          className="w-full p-2 border mb-4 rounded"
          placeholder="Password"
          name="password"
          type="password"
          value={form.password}
          onChange={handleChange}
          autoComplete="new-password"
          disabled={loading}
        />
        <input
          className="w-full p-2 border mb-4 rounded"
          placeholder="Confirm Password"
          name="confirmPassword"
          type="password"
          value={form.confirmPassword}
          onChange={handleChange}
          autoComplete="new-password"
          disabled={loading}
        />

        <button
          type="submit"
          disabled={loading}
          className={`w-full py-2 rounded text-white ${loading ? 'bg-gray-500 cursor-not-allowed' : 'bg-green-600 hover:bg-green-700'
            }`}
        >
          {loading ? "Creating Account..." : "Create Account"}
        </button>
      </form>

      {message && (
        <p className={`mt-4 text-center text-sm ${error ? 'text-red-600' : 'text-green-600'}`}>
          {message}
        </p>
      )}
    </div>
  );
};

export default Signup;
