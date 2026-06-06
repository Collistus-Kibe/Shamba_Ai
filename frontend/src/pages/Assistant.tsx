import React, { useState, useEffect, useRef } from "react";
import api from "../services/api";

interface AssistantProps {
  activeFarmId: number | null;
}

interface Message {
  id: number;
  sender: "user" | "assistant";
  message_text: string;
  media_url?: string;
  created_at: Date;
  diagnosis_report?: any;
}

interface Conversation {
  id: number;
  title: string;
  created_at: string;
}

export const Assistant: React.FC<AssistantProps> = ({ activeFarmId }) => {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [currentConversation, setCurrentConversation] = useState<any | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputText, setInputText] = useState("");
  const [loading, setLoading] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  // ── Image preview state (Gemini-style: attach, type, then send) ──
  const [pendingImage, setPendingImage] = useState<{ file: File; previewUrl: string } | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const chatBottomRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const hasMessages = messages.length > 0 || loading;

  useEffect(() => {
    const initChat = async () => {
      try {
        const convs = await api.getConversations();
        setConversations(convs);
        if (convs.length > 0) {
          const details = await api.getConversationDetails(convs[0].id);
          setCurrentConversation(details);
          setMessages(details.messages || []);
        }
      } catch (e) {
        console.error("Failed to load chat history", e);
      }
    };
    initChat();
  }, []);

  useEffect(() => {
    chatBottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const handleNewChat = async () => {
    setCurrentConversation(null);
    setMessages([]);
    setPendingImage(null);
    setInputText("");
    setSidebarOpen(false);
    setTimeout(() => inputRef.current?.focus(), 100);
  };

  const handleSelectConversation = async (conv: Conversation) => {
    try {
      const details = await api.getConversationDetails(conv.id);
      setCurrentConversation(details);
      setMessages(details.messages || []);
      setPendingImage(null);
      setInputText("");
      setSidebarOpen(false);
    } catch (e) {
      console.error("Failed to load conversation", e);
    }
  };

  const deriveChatTitle = (text: string): string => {
    const crops = ["maize","beans","wheat","rice","tomato","potato","cassava","sorghum","millet","sugarcane","coffee","tea","cotton","sunflower","groundnut","soybean","onion","cabbage","carrot","pepper","avocado","mango","banana","pineapple","watermelon","kale","spinach","peas","cowpeas","pigeon peas"];
    const lower = text.toLowerCase();
    for (const crop of crops) {
      if (lower.includes(crop)) return crop.charAt(0).toUpperCase() + crop.slice(1) + " Analysis";
    }
    if (lower.includes("disease") || lower.includes("diagnos")) return "Crop Diagnosis";
    if (lower.includes("weather")) return "Weather Analysis";
    if (lower.includes("irrigat")) return "Irrigation Advice";
    if (lower.includes("soil")) return "Soil Analysis";
    if (lower.includes("market") || lower.includes("price")) return "Market Analysis";
    return text.length > 30 ? text.substring(0, 30) + "..." : text;
  };

  // ── Combined send: text only, or image + text ──
  const handleSend = async () => {
    const text = inputText.trim();
    const image = pendingImage;

    // Nothing to send
    if (!text && !image) return;

    setInputText("");
    setPendingImage(null);
    if (fileInputRef.current) fileInputRef.current.value = "";

    // Build user message
    const userMsgText = image
      ? (text || "Analyze this plant image")
      : text;
    const userMsg: Message = {
      id: Date.now(),
      sender: "user",
      message_text: userMsgText,
      media_url: image?.previewUrl,
      created_at: new Date(),
    };
    setMessages((prev) => [...prev, userMsg]);
    setLoading(true);

    try {
      let convId = currentConversation?.id;

      // Create conversation if needed
      if (!convId) {
        const title = image ? "Plant Image Diagnosis" : deriveChatTitle(userMsgText);
        const newConv = await api.createConversation(title, activeFarmId || undefined);
        setCurrentConversation(newConv);
        setConversations((prev) => [newConv, ...prev]);
        convId = newConv.id;
      }

      if (image) {
        // ── Image + text → diagnose image, include farmer's text as context ──
        const report = await api.diagnoseCropImage(image.file, undefined, activeFarmId || undefined);
        const farmerNote = text ? `\n\n📝 **Farmer's Note:** "${text}"\n` : "";
        const aiReplyText =
          `🌿 **Disease:** ${report.disease_name}\n` +
          `📊 **Confidence:** ${Math.round(report.confidence * 100)}%\n` +
          `⚠️ **Severity:** ${report.severity}\n` +
          farmerNote + `\n` +
          `**Symptoms:** ${report.symptoms}\n\n` +
          `**Causes:** ${report.causes}\n\n` +
          `💊 **Commercial Treatment:** ${report.treatment_commercial}\n\n` +
          `🌱 **Local Solution:** ${report.treatment_local}\n\n` +
          `🧪 **Traditional Remedy:** ${report.treatment_traditional}\n\n` +
          `🛡️ **Prevention:** ${report.prevention}`;
        // Also save to chat history
        await api.postChatMessage(convId, `[IMAGE DIAGNOSED]: ${report.disease_name}. Farmer said: "${text || "no note"}"`);
        setMessages((prev) => [...prev, {
          id: report.id, sender: "assistant", message_text: aiReplyText,
          created_at: new Date(), diagnosis_report: report,
        }]);
      } else {
        // ── Text only → regular chat ──
        const reply = await api.postChatMessage(convId, userMsgText);
        setMessages((prev) => [...prev, {
          id: reply.id, sender: "assistant", message_text: reply.message_text,
          media_url: reply.media_url, created_at: new Date(reply.created_at),
        }]);
      }
    } catch (e: any) {
      setMessages((prev) => [...prev, {
        id: Date.now() + 1, sender: "assistant",
        message_text: `Sorry, I encountered an error: ${e.message}`,
        created_at: new Date(),
      }]);
    } finally {
      setLoading(false);
    }
  };

  // ── When user picks a file → stage it as preview (don't send yet) ──
  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const previewUrl = URL.createObjectURL(file);
    setPendingImage({ file, previewUrl });
    // Focus the text input so user can type alongside
    setTimeout(() => inputRef.current?.focus(), 100);
  };

  const removePendingImage = () => {
    if (pendingImage) {
      URL.revokeObjectURL(pendingImage.previewUrl);
      setPendingImage(null);
    }
    if (fileInputRef.current) fileInputRef.current.value = "";
  };

  const hasSendableContent = inputText.trim().length > 0 || pendingImage !== null;

  // ── Shared Input Bar Component ──────────────────
  const renderInputBar = (isCenter: boolean) => (
    <div style={{
      display: "flex", flexDirection: "column",
      backgroundColor: "#f0f4f9",
      borderRadius: pendingImage ? "20px" : "28px",
      border: "1px solid #dfe3ea",
      maxWidth: isCenter ? "580px" : "720px",
      width: "100%",
      margin: "0 auto",
      transition: "box-shadow 0.2s, border-color 0.2s",
      overflow: "hidden",
    }}>
      {/* ── Image preview (like Gemini) ── */}
      {pendingImage && (
        <div style={{ padding: "12px 12px 0 12px" }}>
          <div style={{
            position: "relative", display: "inline-block",
            borderRadius: "12px", overflow: "hidden",
            border: "1px solid #e2e8f0",
          }}>
            <img
              src={pendingImage.previewUrl}
              alt="Preview"
              style={{ maxWidth: "140px", maxHeight: "100px", objectFit: "cover", display: "block", borderRadius: "12px" }}
            />
            {/* Remove button */}
            <button onClick={removePendingImage} style={{
              position: "absolute", top: "4px", right: "4px",
              width: "22px", height: "22px", borderRadius: "50%",
              backgroundColor: "rgba(0,0,0,0.6)", border: "none",
              color: "#ffffff", cursor: "pointer",
              display: "flex", alignItems: "center", justifyContent: "center",
            }}>
              <span className="material-symbols-outlined" style={{ fontSize: "14px" }}>close</span>
            </button>
          </div>
        </div>
      )}

      {/* ── Text input row ── */}
      <div style={{ display: "flex", alignItems: "center", padding: "4px" }}>
        {/* (+) button for images */}
        <button
          onClick={() => fileInputRef.current?.click()}
          style={{
            width: "44px", height: "44px", borderRadius: "50%",
            display: "flex", alignItems: "center", justifyContent: "center",
            border: "none", cursor: "pointer", backgroundColor: "transparent",
            color: "#5f6368", flexShrink: 0, transition: "color 0.15s",
          }}
          onMouseOver={(e) => (e.currentTarget.style.color = "#006c49")}
          onMouseOut={(e) => (e.currentTarget.style.color = "#5f6368")}
          title="Upload plant image"
        >
          <span className="material-symbols-outlined" style={{ fontSize: "22px" }}>add</span>
        </button>

        <input
          ref={inputRef}
          type="text"
          placeholder={pendingImage ? "Add details about this plant..." : "Ask Shamba AI"}
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
          onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); handleSend(); } }}
          style={{
            flex: 1, border: "none", backgroundColor: "transparent",
            padding: "12px 4px", fontSize: "16px", outline: "none",
            fontFamily: "'Inter', sans-serif", color: "#1a1a1a",
            lineHeight: "1.5",
          }}
        />

        {hasSendableContent ? (
          <button
            onClick={handleSend}
            style={{
              width: "40px", height: "40px", borderRadius: "50%",
              display: "flex", alignItems: "center", justifyContent: "center",
              border: "none", cursor: "pointer",
              background: "linear-gradient(135deg, #006c49, #003527)",
              color: "#ffffff", flexShrink: 0, marginRight: "2px",
            }}
          >
            <span className="material-symbols-outlined" style={{ fontSize: "20px", fontVariationSettings: "'FILL' 1" }}>arrow_upward</span>
          </button>
        ) : (
          <button
            style={{
              width: "40px", height: "40px", borderRadius: "50%",
              display: "flex", alignItems: "center", justifyContent: "center",
              border: "none", cursor: "pointer", backgroundColor: "transparent",
              color: "#5f6368", flexShrink: 0, marginRight: "2px",
            }}
            title="Voice input (coming soon)"
          >
            <span className="material-symbols-outlined" style={{ fontSize: "22px" }}>mic</span>
          </button>
        )}
      </div>
    </div>
  );

  return (
    <div style={{ display: "flex", flex: 1, overflow: "hidden", fontFamily: "'Inter', sans-serif", position: "relative" }}>
      <input type="file" accept="image/*" ref={fileInputRef} onChange={handleFileChange} style={{ display: "none" }} />

      {/* ── Sidebar ─────────────────────────────── */}
      {sidebarOpen && (
        <div style={{ position: "fixed", inset: 0, zIndex: 100, backgroundColor: "rgba(0,53,39,0.15)", backdropFilter: "blur(4px)" }} onClick={() => setSidebarOpen(false)}>
          <div onClick={(e) => e.stopPropagation()} style={{
            position: "fixed", top: 0, left: 0, bottom: 0, width: "280px",
            backgroundColor: "#f8f9fa", zIndex: 101, display: "flex", flexDirection: "column",
            borderRight: "1px solid #e2e8f0", boxShadow: "4px 0 20px rgba(0,0,0,0.08)",
          }}>
            <div style={{ padding: "16px 20px", display: "flex", alignItems: "center", justifyContent: "space-between", borderBottom: "1px solid #e2e8f0" }}>
              <span style={{ fontSize: "16px", fontWeight: 700, color: "#003527" }}>Chats</span>
              <button onClick={() => setSidebarOpen(false)} style={{ border: "none", background: "none", cursor: "pointer", color: "#5f6368", display: "flex" }}>
                <span className="material-symbols-outlined">close</span>
              </button>
            </div>
            <button onClick={handleNewChat} style={{
              display: "flex", alignItems: "center", gap: "8px", padding: "10px 16px", margin: "12px 16px",
              borderRadius: "12px", border: "1.5px solid #c4c7c5", backgroundColor: "#ffffff",
              color: "#003527", fontSize: "14px", fontWeight: 600, cursor: "pointer", fontFamily: "'Inter', sans-serif",
            }}
              onMouseOver={(e) => e.currentTarget.style.backgroundColor = "#e8f5e9"}
              onMouseOut={(e) => e.currentTarget.style.backgroundColor = "#ffffff"}
            >
              <span className="material-symbols-outlined" style={{ fontSize: "20px" }}>add</span>
              New Chat
            </button>
            <div style={{ flex: 1, overflowY: "auto" }}>
              {conversations.map((conv) => (
                <div key={conv.id} onClick={() => handleSelectConversation(conv)}
                  style={{
                    display: "flex", alignItems: "center", gap: "10px", padding: "12px 20px", cursor: "pointer",
                    backgroundColor: currentConversation?.id === conv.id ? "#e0f2f1" : "transparent",
                    borderLeft: currentConversation?.id === conv.id ? "3px solid #006c49" : "3px solid transparent",
                    fontSize: "14px", fontWeight: currentConversation?.id === conv.id ? 600 : 400,
                    color: currentConversation?.id === conv.id ? "#003527" : "#404944",
                  }}
                  onMouseOver={(e) => { if (currentConversation?.id !== conv.id) (e.currentTarget).style.backgroundColor = "#e8f5e9"; }}
                  onMouseOut={(e) => { if (currentConversation?.id !== conv.id) (e.currentTarget).style.backgroundColor = "transparent"; }}
                >
                  <span className="material-symbols-outlined" style={{ fontSize: "18px", color: "#707974" }}>chat_bubble_outline</span>
                  <span style={{ overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{conv.title}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* ── Main Chat Area ──────────────────────── */}
      <div style={{ flex: 1, display: "flex", flexDirection: "column", backgroundColor: "#ffffff", overflow: "hidden" }}>

        {/* Sub-header */}
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "8px 16px", borderBottom: hasMessages ? "1px solid #f0f3f5" : "none" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
            <button onClick={() => setSidebarOpen(true)} style={{ width: "40px", height: "40px", borderRadius: "50%", display: "flex", alignItems: "center", justifyContent: "center", border: "none", cursor: "pointer", backgroundColor: "transparent", color: "#003527" }}>
              <span className="material-symbols-outlined" style={{ fontSize: "22px" }}>menu</span>
            </button>
            {hasMessages && (
              <span style={{ fontSize: "15px", fontWeight: 600, color: "#003527" }}>
                {currentConversation?.title || "New Chat"}
              </span>
            )}
          </div>
          <button onClick={handleNewChat} style={{ width: "40px", height: "40px", borderRadius: "50%", display: "flex", alignItems: "center", justifyContent: "center", border: "none", cursor: "pointer", backgroundColor: "transparent", color: "#006c49" }} title="New Chat">
            <span className="material-symbols-outlined" style={{ fontSize: "22px" }}>edit_square</span>
          </button>
        </div>

        {/* ═══ EMPTY STATE (Gemini-style centered) ═══ */}
        {!hasMessages && (
          <div style={{
            flex: 1, display: "flex", flexDirection: "column",
            alignItems: "center", justifyContent: "center",
            padding: "0 24px 80px 24px",
          }}>
            <h1 style={{
              fontSize: "32px", fontWeight: 600, color: "#003527",
              margin: "0 0 32px 0", textAlign: "center",
              background: "linear-gradient(135deg, #003527, #006c49, #00a86b)",
              WebkitBackgroundClip: "text",
              WebkitTextFillColor: "transparent",
              lineHeight: 1.3,
            }}>
              Hello, how can I help<br/>your farm today?
            </h1>

            {renderInputBar(true)}

            <div style={{ display: "flex", flexWrap: "wrap", gap: "8px", justifyContent: "center", marginTop: "20px", maxWidth: "580px" }}>
              {[
                { icon: "psychiatry", label: "Diagnose my crop", action: "Diagnose my crop. I've noticed some issues with my plants." },
                { icon: "add_photo_alternate", label: "Analyze image", action: "__photo__" },
                { icon: "thunderstorm", label: "Weather risks", action: "Check weather risks and forecast for my farming area." },
                { icon: "water_drop", label: "Irrigation advice", action: "Give me professional irrigation advice for my crops." },
              ].map((chip) => (
                <button key={chip.label}
                  onClick={() => chip.action === "__photo__" ? fileInputRef.current?.click() : handleSend()}
                  onClickCapture={() => { if (chip.action !== "__photo__") setInputText(chip.action); }}
                  style={{
                    display: "flex", alignItems: "center", gap: "6px",
                    padding: "8px 16px", borderRadius: "20px",
                    border: "1px solid #c4c7c5", backgroundColor: "#ffffff",
                    color: "#3c4043", fontSize: "13px", fontWeight: 500,
                    cursor: "pointer", fontFamily: "'Inter', sans-serif",
                  }}
                  onMouseOver={(e) => { e.currentTarget.style.backgroundColor = "#f0f4f9"; }}
                  onMouseOut={(e) => { e.currentTarget.style.backgroundColor = "#ffffff"; }}
                >
                  <span className="material-symbols-outlined" style={{ fontSize: "16px", color: "#006c49" }}>{chip.icon}</span>
                  {chip.label}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* ═══ MESSAGES STATE ═══ */}
        {hasMessages && (
          <>
            <div style={{ flex: 1, overflowY: "auto", padding: "20px 16px 140px 16px", display: "flex", flexDirection: "column", gap: "20px" }} className="no-scrollbar">

              {messages.map((msg) => (
                <div key={msg.id}>
                  {msg.sender === "user" ? (
                    <div style={{ display: "flex", justifyContent: "flex-end" }}>
                      <div style={{
                        maxWidth: "70%", backgroundColor: "#003527", color: "#ffffff",
                        padding: "12px 18px", borderRadius: "20px 20px 4px 20px",
                        fontSize: "15px", lineHeight: "1.6", whiteSpace: "pre-line",
                      }}>
                        {msg.media_url && (
                          <img src={msg.media_url} alt="Uploaded" style={{ maxWidth: "220px", maxHeight: "160px", borderRadius: "12px", objectFit: "cover", marginBottom: "8px", display: "block" }} />
                        )}
                        {msg.message_text}
                      </div>
                    </div>
                  ) : (
                    <div style={{ display: "flex", alignItems: "flex-start", gap: "12px", maxWidth: "85%" }}>
                      <div style={{
                        width: "30px", height: "30px", borderRadius: "50%", flexShrink: 0,
                        background: "linear-gradient(135deg, #006c49, #003527)",
                        display: "flex", alignItems: "center", justifyContent: "center", marginTop: "2px",
                      }}>
                        <span className="material-symbols-outlined" style={{ color: "#fff", fontSize: "16px", fontVariationSettings: "'FILL' 1" }}>eco</span>
                      </div>
                      <div style={{
                        backgroundColor: "#f8f9fa", color: "#1a1a1a",
                        padding: "14px 18px", borderRadius: "4px 20px 20px 20px",
                        fontSize: "15px", lineHeight: "1.7", whiteSpace: "pre-line",
                        border: "1px solid #e8eaed",
                      }}>
                        {msg.message_text}
                      </div>
                    </div>
                  )}
                </div>
              ))}

              {loading && (
                <div style={{ display: "flex", alignItems: "flex-start", gap: "12px" }}>
                  <div style={{
                    width: "30px", height: "30px", borderRadius: "50%", flexShrink: 0,
                    background: "linear-gradient(135deg, #006c49, #003527)",
                    display: "flex", alignItems: "center", justifyContent: "center",
                  }}>
                    <span className="material-symbols-outlined" style={{ color: "#fff", fontSize: "16px", fontVariationSettings: "'FILL' 1" }}>eco</span>
                  </div>
                  <div style={{
                    backgroundColor: "#f8f9fa", padding: "16px 24px", borderRadius: "4px 20px 20px 20px",
                    display: "flex", gap: "6px", alignItems: "center", border: "1px solid #e8eaed",
                  }}>
                    <div style={{ width: "8px", height: "8px", borderRadius: "50%", backgroundColor: "#006c49", animation: "shambaTyping 1.4s infinite ease-in-out", animationDelay: "0s" }} />
                    <div style={{ width: "8px", height: "8px", borderRadius: "50%", backgroundColor: "#006c49", animation: "shambaTyping 1.4s infinite ease-in-out", animationDelay: "0.2s" }} />
                    <div style={{ width: "8px", height: "8px", borderRadius: "50%", backgroundColor: "#006c49", animation: "shambaTyping 1.4s infinite ease-in-out", animationDelay: "0.4s" }} />
                    <style>{`@keyframes shambaTyping { 0%, 80%, 100% { transform: scale(0.6); opacity: 0.4; } 40% { transform: scale(1); opacity: 1; } }`}</style>
                  </div>
                </div>
              )}

              <div ref={chatBottomRef} />
            </div>

            {/* Bottom input (when chatting) */}
            <div style={{
              position: "fixed", bottom: "48px", left: 0, right: 0,
              padding: "10px 16px 12px 16px", backgroundColor: "#ffffff",
              borderTop: "1px solid #f0f3f5", zIndex: 40,
            }}>
              {renderInputBar(false)}
            </div>
          </>
        )}
      </div>
    </div>
  );
};

export default Assistant;
