import React, { useState } from "react";
import api from "../services/api";
import { signInWithGoogle } from "../services/firebase";

interface AuthProps {
  onAuthSuccess: () => void;
}

export const Auth: React.FC<AuthProps> = ({ onAuthSuccess }) => {
  const [showEmailForm, setShowEmailForm] = useState(false);
  const [isLogin, setIsLogin] = useState(true);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      if (isLogin) {
        await api.login(email, password);
      } else {
        await api.register(email, password, fullName);
        await api.login(email, password);
      }
      onAuthSuccess();
    } catch (err: any) {
      setError(err.message || "Authentication failed. Please check your credentials.");
    } finally {
      setLoading(false);
    }
  };

  const handleGoogleLogin = async () => {
    setError(null);
    setLoading(true);
    try {
      // Real Firebase Google Sign-In popup
      const { idToken, displayName } = await signInWithGoogle();
      // Send the Firebase ID token to our backend for verification
      await api.loginFirebase(idToken, displayName || undefined);
      onAuthSuccess();
    } catch (err: any) {
      // Don't show error if user simply closed the popup
      if (err?.code === "auth/popup-closed-by-user" || err?.code === "auth/cancelled-popup-request") {
        setLoading(false);
        return;
      }
      setError(err.message || "Google Sign-In failed.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      style={{
        minHeight: "100vh",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        background: "linear-gradient(135deg, #e8f5e9 0%, #f0f4ff 50%, #e0f2f1 100%)",
        padding: "24px",
        fontFamily: "'Inter', sans-serif",
      }}
    >
      <div
        style={{
          width: "100%",
          maxWidth: "420px",
          backgroundColor: "#ffffff",
          borderRadius: "20px",
          boxShadow: "0 8px 32px rgba(0, 53, 39, 0.08), 0 2px 8px rgba(0, 0, 0, 0.04)",
          padding: "48px 36px",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          gap: "8px",
        }}
      >
        {/* Logo Icon */}
        <div
          style={{
            width: "64px",
            height: "64px",
            borderRadius: "16px",
            background: "linear-gradient(135deg, #006c49, #003527)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            marginBottom: "8px",
            boxShadow: "0 4px 16px rgba(0, 108, 73, 0.25)",
          }}
        >
          <span
            className="material-symbols-outlined"
            style={{ color: "#fff", fontSize: "36px", fontVariationSettings: "'FILL' 1" }}
          >
            eco
          </span>
        </div>

        {/* Title */}
        <h1
          style={{
            fontSize: "28px",
            fontWeight: 700,
            color: "#003527",
            margin: 0,
            letterSpacing: "-0.5px",
            textAlign: "center",
          }}
        >
          Shamba <span style={{ color: "#006c49" }}>AI</span>
        </h1>

        {/* Subtitle */}
        <p
          style={{
            fontSize: "14px",
            color: "#707974",
            margin: "0 0 16px 0",
            textAlign: "center",
            lineHeight: "1.5",
            fontWeight: 500,
          }}
        >
          AI-Powered Agricultural Intelligence
        </p>

        {/* Error Message */}
        {error && (
          <div
            style={{
              width: "100%",
              padding: "12px 16px",
              borderRadius: "12px",
              backgroundColor: "#ffdad6",
              color: "#93000a",
              fontSize: "13px",
              fontWeight: 500,
              display: "flex",
              alignItems: "center",
              gap: "8px",
            }}
          >
            <span className="material-symbols-outlined" style={{ fontSize: "18px" }}>error</span>
            <span>{error}</span>
          </div>
        )}

        {/* Google Sign-In Button */}
        <button
          onClick={handleGoogleLogin}
          disabled={loading}
          style={{
            width: "100%",
            padding: "14px 24px",
            borderRadius: "12px",
            border: "1.5px solid #bfc9c3",
            backgroundColor: "#ffffff",
            color: "#151c27",
            fontSize: "15px",
            fontWeight: 600,
            cursor: "pointer",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            gap: "10px",
            transition: "all 0.2s ease",
            fontFamily: "'Inter', sans-serif",
            opacity: loading ? 0.6 : 1,
          }}
          onMouseOver={(e) => { if (!loading) (e.currentTarget.style.backgroundColor = "#f0f3ff"); }}
          onMouseOut={(e) => { (e.currentTarget.style.backgroundColor = "#ffffff"); }}
        >
          <svg width="20" height="20" viewBox="0 0 48 48">
            <path fill="#EA4335" d="M24 9.5c3.54 0 6.71 1.22 9.21 3.6l6.85-6.85C35.9 2.38 30.47 0 24 0 14.62 0 6.51 5.38 2.56 13.22l7.98 6.19C12.43 13.72 17.74 9.5 24 9.5z"/>
            <path fill="#4285F4" d="M46.98 24.55c0-1.57-.15-3.09-.38-4.55H24v9.02h12.94c-.58 2.96-2.26 5.48-4.78 7.18l7.73 6c4.51-4.18 7.09-10.36 7.09-17.65z"/>
            <path fill="#FBBC05" d="M10.53 28.59c-.48-1.45-.76-2.99-.76-4.59s.27-3.14.76-4.59l-7.98-6.19C.92 16.46 0 20.12 0 24c0 3.88.92 7.54 2.56 10.78l7.97-6.19z"/>
            <path fill="#34A853" d="M24 48c6.48 0 11.93-2.13 15.89-5.81l-7.73-6c-2.15 1.45-4.92 2.3-8.16 2.3-6.26 0-11.57-4.22-13.47-9.91l-7.98 6.19C6.51 42.62 14.62 48 24 48z"/>
          </svg>
          {loading ? "Signing in..." : "Sign In with Google"}
        </button>

        {/* Divider */}
        {!showEmailForm && (
          <button
            onClick={() => setShowEmailForm(true)}
            style={{
              background: "none",
              border: "none",
              color: "#006c49",
              fontSize: "13px",
              fontWeight: 600,
              cursor: "pointer",
              padding: "8px 0 0 0",
              fontFamily: "'JetBrains Mono', monospace",
            }}
          >
            Or sign in with email
          </button>
        )}

        {/* Email Login Form (expandable) */}
        {showEmailForm && (
          <>
            <div
              style={{
                width: "100%",
                display: "flex",
                alignItems: "center",
                gap: "12px",
                margin: "8px 0",
              }}
            >
              <div style={{ flex: 1, height: "1px", backgroundColor: "#bfc9c3" }} />
              <span style={{ fontSize: "11px", color: "#707974", fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.08em", fontFamily: "'JetBrains Mono', monospace" }}>
                or use email
              </span>
              <div style={{ flex: 1, height: "1px", backgroundColor: "#bfc9c3" }} />
            </div>

            <form
              onSubmit={handleSubmit}
              style={{
                width: "100%",
                display: "flex",
                flexDirection: "column",
                gap: "14px",
              }}
            >
              {!isLogin && (
                <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
                  <label style={{ fontSize: "12px", fontWeight: 600, color: "#404944", fontFamily: "'JetBrains Mono', monospace" }}>
                    Full Name
                  </label>
                  <input
                    type="text"
                    placeholder="e.g. John Doe"
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                    required={!isLogin}
                    style={{
                      width: "100%",
                      padding: "12px 16px",
                      borderRadius: "10px",
                      border: "1.5px solid #bfc9c3",
                      fontSize: "15px",
                      fontFamily: "'Inter', sans-serif",
                      color: "#151c27",
                      backgroundColor: "#f9f9ff",
                      outline: "none",
                      transition: "border-color 0.2s",
                      boxSizing: "border-box",
                    }}
                    onFocus={(e) => { e.currentTarget.style.borderColor = "#006c49"; }}
                    onBlur={(e) => { e.currentTarget.style.borderColor = "#bfc9c3"; }}
                  />
                </div>
              )}

              <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
                <label style={{ fontSize: "12px", fontWeight: 600, color: "#404944", fontFamily: "'JetBrains Mono', monospace" }}>
                  Email Address
                </label>
                <input
                  type="email"
                  placeholder="farmer@shamba.ai"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  style={{
                    width: "100%",
                    padding: "12px 16px",
                    borderRadius: "10px",
                    border: "1.5px solid #bfc9c3",
                    fontSize: "15px",
                    fontFamily: "'Inter', sans-serif",
                    color: "#151c27",
                    backgroundColor: "#f9f9ff",
                    outline: "none",
                    transition: "border-color 0.2s",
                    boxSizing: "border-box",
                  }}
                  onFocus={(e) => { e.currentTarget.style.borderColor = "#006c49"; }}
                  onBlur={(e) => { e.currentTarget.style.borderColor = "#bfc9c3"; }}
                />
              </div>

              <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
                <label style={{ fontSize: "12px", fontWeight: 600, color: "#404944", fontFamily: "'JetBrains Mono', monospace" }}>
                  Password
                </label>
                <input
                  type="password"
                  placeholder="••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  style={{
                    width: "100%",
                    padding: "12px 16px",
                    borderRadius: "10px",
                    border: "1.5px solid #bfc9c3",
                    fontSize: "15px",
                    fontFamily: "'Inter', sans-serif",
                    color: "#151c27",
                    backgroundColor: "#f9f9ff",
                    outline: "none",
                    transition: "border-color 0.2s",
                    boxSizing: "border-box",
                  }}
                  onFocus={(e) => { e.currentTarget.style.borderColor = "#006c49"; }}
                  onBlur={(e) => { e.currentTarget.style.borderColor = "#bfc9c3"; }}
                />
              </div>

              <button
                type="submit"
                disabled={loading}
                style={{
                  width: "100%",
                  padding: "14px",
                  borderRadius: "12px",
                  border: "none",
                  background: "linear-gradient(135deg, #006c49, #003527)",
                  color: "#ffffff",
                  fontSize: "15px",
                  fontWeight: 600,
                  cursor: "pointer",
                  fontFamily: "'Inter', sans-serif",
                  opacity: loading ? 0.6 : 1,
                  transition: "opacity 0.2s",
                }}
              >
                {loading ? "Processing..." : isLogin ? "Sign In" : "Register"}
              </button>

              <button
                type="button"
                onClick={() => setIsLogin(!isLogin)}
                style={{
                  background: "none",
                  border: "none",
                  color: "#006c49",
                  fontSize: "13px",
                  fontWeight: 600,
                  cursor: "pointer",
                  padding: "4px 0 0 0",
                  fontFamily: "'JetBrains Mono', monospace",
                  textAlign: "center",
                }}
              >
                {isLogin ? "New to Shamba AI? Register here" : "Already have an account? Sign in"}
              </button>
            </form>
          </>
        )}
      </div>
    </div>
  );
};

export default Auth;
