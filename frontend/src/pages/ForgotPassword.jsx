import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useUser } from "../context/UserContext";
import { apiFetch } from "@/services/api";

export default function ForgotPassword() {
    const [step, setStep] = useState(1); // 1 = enter email, 2 = set new password
    const [email, setEmail] = useState("");
    const [newPassword, setNewPassword] = useState("");
    const [confirmPassword, setConfirmPassword] = useState("");
    const [message, setMessage] = useState("");
    const [error, setError] = useState(false);
    const navigate = useNavigate();
    const { login } = useUser();

    const handleEmailSubmit = async (e) => {
        e.preventDefault();
        setMessage("");
        setError(false);

        if (!email) {
            setMessage("🚫 Please enter your email.");
            setError(true);
            return;
        }

        try {
            const res = await apiFetch("/api/users/forgot-password", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ email }),
            });

            if (res.ok) {
                setMessage("✅ Email found. Please enter your new password.");
                setError(false);
                setStep(2);
            } else {
                const data = await res.json();
                setMessage(data.detail || "🚫 Error processing your request.");
                setError(true);
            }
        } catch {
            setMessage("🚫 Network error. Please try again.");
            setError(true);
        }
    };

    const handlePasswordReset = async (e) => {
        e.preventDefault();
        setMessage("");
        setError(false);

        if (!newPassword || !confirmPassword) {
            setMessage("🚫 Please fill in all password fields.");
            setError(true);
            return;
        }
        if (newPassword !== confirmPassword) {
            setMessage("🚫 Passwords do not match.");
            setError(true);
            return;
        }

        try {
            const res = await apiFetch("/api/users/reset-password", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    email,
                    new_password: newPassword,
                    confirm_password: confirmPassword,
                }),
            });

            if (res.ok) {
                const data = await res.json();
                login(data); // Automatically log in user with token & user data
                setMessage("✅ Password reset successful! Redirecting...");
                setTimeout(() => navigate("/"), 1500);
            } else {
                const data = await res.json();
                setMessage(data.detail || "🚫 Error resetting password.");
                setError(true);
            }
        } catch {
            setMessage("🚫 Network error. Please try again.");
            setError(true);
        }
    };

    return (
        <div className="max-w-sm mx-auto mt-8">
            <h2 className="text-2xl font-semibold mb-4">
                {step === 1 ? "Forgot Password" : "Reset Password"}
            </h2>

            {step === 1 && (
                <form onSubmit={handleEmailSubmit}>
                    <input
                        type="email"
                        placeholder="Enter your email"
                        className="w-full p-2 border mb-4 rounded"
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        autoComplete="email"
                    />
                    <button
                        type="submit"
                        className="w-full bg-blue-600 text-white py-2 rounded hover:bg-blue-700"
                    >
                        Next
                    </button>
                </form>
            )}

            {step === 2 && (
                <form onSubmit={handlePasswordReset}>
                    <input
                        type="password"
                        placeholder="New Password"
                        className="w-full p-2 border mb-4 rounded"
                        value={newPassword}
                        onChange={(e) => setNewPassword(e.target.value)}
                        autoComplete="new-password"
                    />
                    <input
                        type="password"
                        placeholder="Confirm New Password"
                        className="w-full p-2 border mb-4 rounded"
                        value={confirmPassword}
                        onChange={(e) => setConfirmPassword(e.target.value)}
                        autoComplete="new-password"
                    />
                    <button
                        type="submit"
                        className="w-full bg-green-600 text-white py-2 rounded hover:bg-green-700"
                    >
                        Reset Password
                    </button>
                </form>
            )}

            {message && (
                <p
                    className={`mt-4 text-center text-sm ${error ? "text-red-600" : "text-green-600"
                        }`}
                >
                    {message}
                </p>
            )}
        </div>
    );
}
