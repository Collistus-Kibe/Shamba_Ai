import { useEffect, useState } from "react";
import Auth from "./pages/Auth";
import Assistant from "./pages/Assistant";
import Market from "./pages/Market";
import api from "./services/api";

type Tab = "assistant" | "market";

export function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [user, setUser] = useState<any>(null);
  const [activeTab, setActiveTab] = useState<Tab>("assistant");
  const [menuOpen, setMenuOpen] = useState(false);

  const checkAuth = () => {
    const token = localStorage.getItem("shamba_token");
    const storedUser = localStorage.getItem("shamba_user");
    if (token && storedUser) {
      setIsAuthenticated(true);
      setUser(JSON.parse(storedUser));
    } else {
      setIsAuthenticated(false);
      setUser(null);
    }
  };

  useEffect(() => {
    checkAuth();
    window.addEventListener("auth-changed", checkAuth);
    return () => window.removeEventListener("auth-changed", checkAuth);
  }, []);

  const handleLogout = () => {
    api.logout();
    setMenuOpen(false);
  };

  if (!isAuthenticated) {
    return <Auth onAuthSuccess={checkAuth} />;
  }

  return (
    <div style={{
      minHeight: "100vh",
      display: "flex",
      flexDirection: "column",
      backgroundColor: "#f9f9ff",
      fontFamily: "'Inter', sans-serif",
      overflow: "hidden",
    }}>

      {/* ── Top Bar ───────────────────────────────────── */}
      <header style={{
        position: "sticky",
        top: 0,
        zIndex: 40,
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        padding: "0 20px",
        height: "56px",
        backgroundColor: "#ffffff",
        borderBottom: "1px solid #e2e8f8",
        boxShadow: "0 1px 4px rgba(0,0,0,0.03)",
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
          <div style={{
            width: "36px", height: "36px", borderRadius: "10px",
            background: "linear-gradient(135deg, #006c49, #003527)",
            display: "flex", alignItems: "center", justifyContent: "center",
          }}>
            <span className="material-symbols-outlined" style={{ color: "#fff", fontSize: "22px", fontVariationSettings: "'FILL' 1" }}>eco</span>
          </div>
          <span style={{ fontSize: "18px", fontWeight: 700, color: "#003527", letterSpacing: "-0.3px" }}>
            Shamba <span style={{ color: "#006c49" }}>AI</span>
          </span>
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
          <button
            onClick={() => setMenuOpen(!menuOpen)}
            style={{
              width: "36px", height: "36px", borderRadius: "50%",
              backgroundColor: "#064e3b", color: "#80bea6",
              display: "flex", alignItems: "center", justifyContent: "center",
              border: "2px solid #bfc9c3", cursor: "pointer",
              fontSize: "15px", fontWeight: 700, fontFamily: "'Inter', sans-serif",
            }}
          >
            {user?.full_name?.charAt(0).toUpperCase() || user?.email?.charAt(0).toUpperCase() || "U"}
          </button>
        </div>
      </header>

      {/* ── User Menu Drawer ─────────────────────────── */}
      {menuOpen && (
        <div
          onClick={() => setMenuOpen(false)}
          style={{
            position: "fixed", inset: 0, zIndex: 9999,
            backgroundColor: "rgba(0,53,39,0.15)", backdropFilter: "blur(4px)",
          }}
        >
          <div
            onClick={(e) => e.stopPropagation()}
            style={{
              position: "absolute", top: "60px", right: "16px",
              width: "260px", backgroundColor: "#ffffff",
              borderRadius: "16px", boxShadow: "0 12px 40px rgba(0,0,0,0.12)",
              padding: "20px", display: "flex", flexDirection: "column", gap: "16px",
            }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: "12px", paddingBottom: "12px", borderBottom: "1px solid #e2e8f8" }}>
              <div style={{
                width: "40px", height: "40px", borderRadius: "50%",
                backgroundColor: "#064e3b", color: "#80bea6",
                display: "flex", alignItems: "center", justifyContent: "center",
                fontWeight: 700, fontSize: "16px",
              }}>
                {user?.full_name?.charAt(0).toUpperCase() || "U"}
              </div>
              <div>
                <div style={{ fontSize: "14px", fontWeight: 600, color: "#151c27" }}>{user?.full_name || "Farmer"}</div>
                <div style={{ fontSize: "12px", color: "#707974" }}>{user?.email}</div>
              </div>
            </div>

            <button
              onClick={handleLogout}
              style={{
                display: "flex", alignItems: "center", gap: "10px",
                padding: "12px 16px", borderRadius: "10px",
                border: "1px solid #ffdad6", backgroundColor: "#fff",
                color: "#ba1a1a", fontSize: "14px", fontWeight: 600,
                cursor: "pointer", fontFamily: "'Inter', sans-serif",
                transition: "background-color 0.2s",
              }}
              onMouseOver={(e) => e.currentTarget.style.backgroundColor = "#ffdad6"}
              onMouseOut={(e) => e.currentTarget.style.backgroundColor = "#fff"}
            >
              <span className="material-symbols-outlined" style={{ fontSize: "20px" }}>logout</span>
              Sign Out
            </button>
          </div>
        </div>
      )}

      {/* ── Main Content Area ─────────────────────────── */}
      <div style={{ flex: 1, display: "flex", flexDirection: "column", overflow: "hidden", paddingBottom: "48px" }}>
        {activeTab === "assistant" && <Assistant activeFarmId={null} />}
        {activeTab === "market" && <Market />}
      </div>

      {/* ── Bottom Tab Bar (slim, 2 tabs) ────────────── */}
      <nav style={{
        position: "fixed", bottom: 0, left: 0, width: "100%", zIndex: 50,
        display: "flex", justifyContent: "center", alignItems: "center",
        padding: "6px 60px 8px 60px",
        backgroundColor: "#ffffff",
        borderTop: "1px solid #e2e8f8",
      }}>
        {[
          { id: "assistant" as Tab, icon: "smart_toy", label: "Assistant" },
          { id: "market" as Tab, icon: "storefront", label: "Market" },
        ].map((tab) => {
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              style={{
                flex: 1, display: "flex", flexDirection: "column", alignItems: "center", gap: "1px",
                padding: "4px 0", border: "none", cursor: "pointer",
                fontFamily: "'Inter', sans-serif", fontSize: "10px", fontWeight: isActive ? 700 : 500,
                backgroundColor: "transparent",
                color: isActive ? "#003527" : "#707974",
                transition: "color 0.2s",
                position: "relative",
              }}
            >
              {isActive && (
                <div style={{
                  position: "absolute", top: "-6px", left: "50%", transform: "translateX(-50%)",
                  width: "32px", height: "3px", borderRadius: "2px",
                  backgroundColor: "#006c49",
                }} />
              )}
              <span className="material-symbols-outlined" style={{
                fontSize: "22px",
                fontVariationSettings: isActive ? "'FILL' 1" : "'FILL' 0",
              }}>{tab.icon}</span>
              {tab.label}
            </button>
          );
        })}
      </nav>


    </div>
  );
}

export default App;
