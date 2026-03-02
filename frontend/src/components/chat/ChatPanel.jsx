import { useEffect, useRef, useState } from "react";
import { X, Send, Trash2, ChevronDown } from "lucide-react";
import { useChat } from "../../hooks/useChat";
import MessageBubble from "./MessageBubble";
import ToolCallVisualizer from "./ToolCallVisualizer";
import AppListInput from "./AppListInput";

const SUGGESTIONS = [
  "Best iPhone for photography?",
  "I want the lightest iPhone possible",
  "Best value under $900?",
  "Compare Pro vs Air for video",
];

export default function ChatPanel({ isOpen, onClose }) {
  const { messages, streaming, activeTool, sendMessage, clearMessages } = useChat();
  const [input, setInput] = useState("");
  const [showApps, setShowApps] = useState(false);
  const bottomRef = useRef(null);

  // Auto-scroll on new content
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, activeTool]);

  const handleSend = () => {
    if (!input.trim() || streaming) return;
    sendMessage(input.trim());
    setInput("");
  };

  const handleKeyDown = e => {
    if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); handleSend(); }
  };

  return (
    <>
      {/* Backdrop */}
      {isOpen && <div className="fixed inset-0 bg-black/20 z-40" onClick={onClose} />}

      {/* Panel */}
      <div
        className="fixed top-0 right-0 bottom-0 z-50 flex flex-col bg-white shadow-2xl transition-transform duration-300"
        style={{
          width: "min(55vw, 680px)",
          transform: isOpen ? "translateX(0)" : "translateX(100%)",
          borderLeft: "1px solid #E5E5EA",
        }}>

        {/* Header */}
        <div className="flex items-center justify-between px-5 py-4" style={{ borderBottom: "1px solid #E5E5EA" }}>
          <div>
            <h2 className="font-semibold text-sm text-apple-dark">iPhone Advisor</h2>
            <p className="text-xs text-apple-light mt-0.5">Powered by real reviews + specs</p>
          </div>
          <div className="flex items-center gap-2">
            {messages.length > 0 && (
              <button onClick={clearMessages} className="p-1.5 rounded-full hover:bg-gray-100 transition-colors" title="Clear chat">
                <Trash2 size={14} className="text-apple-light" />
              </button>
            )}
            <button onClick={onClose} className="p-1.5 rounded-full hover:bg-gray-100 transition-colors">
              <X size={16} className="text-apple-dark" />
            </button>
          </div>
        </div>

        {/* App list toggle */}
        <button
          onClick={() => setShowApps(v => !v)}
          className="flex items-center justify-between px-5 py-2.5 text-xs font-medium text-apple-light hover:bg-gray-50 transition-colors"
          style={{ borderBottom: "1px solid #E5E5EA" }}>
          <span>📱 Recommend from my app list</span>
          <ChevronDown size={13} className={`transition-transform ${showApps ? "rotate-180" : ""}`} />
        </button>
        {showApps && <AppListInput onSubmit={(msg, apps) => { sendMessage(msg, apps); setShowApps(false); }} />}

        {/* Messages */}
        <div className="flex-1 overflow-y-auto px-4 py-4 scrollbar-hide">
          {messages.length === 0 && (
            <div className="space-y-3">
              <p className="text-center text-xs text-apple-light py-4">
                Ask me anything about iPhone 17 models.<br />I'll use real specs and review data.
              </p>
              <div className="space-y-2">
                {SUGGESTIONS.map(s => (
                  <button key={s} onClick={() => sendMessage(s)}
                    className="w-full text-left px-4 py-3 rounded-2xl text-sm text-apple-dark hover:bg-gray-50 transition-colors"
                    style={{ border: "1px solid #E5E5EA", background: "#fff" }}>
                    {s}
                  </button>
                ))}
              </div>
            </div>
          )}

          {messages.map((msg, i) => <MessageBubble key={i} message={msg} />)}
          <ToolCallVisualizer tool={activeTool} />
          <div ref={bottomRef} />
        </div>

        {/* Input */}
        <div className="px-4 py-4" style={{ borderTop: "1px solid #E5E5EA" }}>
          <div className="flex items-end gap-2 px-4 py-2 rounded-2xl" style={{ border: "1.5px solid #D2D2D7" }}>
            <textarea
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask about any iPhone…"
              rows={4}
              disabled={streaming}
              className="flex-1 text-sm resize-none outline-none bg-transparent leading-relaxed text-apple-dark placeholder:text-apple-light"
              style={{ maxHeight: 120 }}
            />
            <button
              onClick={handleSend}
              disabled={!input.trim() || streaming}
              className="p-1.5 rounded-full transition-colors flex-shrink-0 disabled:opacity-30"
              style={{ background: "#0071E3" }}>
              <Send size={13} className="text-white" />
            </button>
          </div>
          <p className="text-center text-[10px] text-apple-light mt-2">Grounded in 8,700+ real reviews</p>
        </div>
      </div>
    </>
  );
}
