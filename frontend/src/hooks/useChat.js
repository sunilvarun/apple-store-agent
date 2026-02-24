import { useState, useRef, useCallback } from "react";
import { v4 as uuidv4 } from "uuid";

export function useChat() {
  const [messages, setMessages]       = useState([]);
  const [streaming, setStreaming]     = useState(false);
  const [activeTool, setActiveTool]   = useState(null);
  const sessionId = useRef(uuidv4());
  const bufferRef = useRef("");

  const appendToLast = useCallback((text) => {
    setMessages(prev => {
      const msgs = [...prev];
      if (msgs.length && msgs[msgs.length - 1].role === "assistant") {
        msgs[msgs.length - 1] = { ...msgs[msgs.length - 1], content: msgs[msgs.length - 1].content + text };
      }
      return msgs;
    });
  }, []);

  const sendMessage = useCallback(async (userText, appList = []) => {
    if (streaming) return;
    setStreaming(true);
    bufferRef.current = "";

    setMessages(prev => [
      ...prev,
      { role: "user", content: userText },
      { role: "assistant", content: "", streaming: true },
    ]);

    try {
      const resp = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          messages: [{ role: "user", content: userText }],
          session_id: sessionId.current,
          app_list: appList,
        }),
      });

      const reader = resp.body.getReader();
      const decoder = new TextDecoder();

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        const lines = chunk.split("\n");

        for (const line of lines) {
          if (!line.startsWith("data: ")) continue;
          try {
            const event = JSON.parse(line.slice(6));
            if (event.type === "text") {
              appendToLast(event.content);
            } else if (event.type === "tool_use") {
              setActiveTool(event.tool);
            } else if (event.type === "tool_result") {
              setActiveTool(null);
            } else if (event.type === "done") {
              setMessages(prev => {
                const msgs = [...prev];
                if (msgs.length) msgs[msgs.length - 1] = { ...msgs[msgs.length - 1], streaming: false };
                return msgs;
              });
              setStreaming(false);
            } else if (event.type === "error") {
              appendToLast(`\n\n⚠️ Error: ${event.message}`);
              setStreaming(false);
            }
          } catch {}
        }
      }
    } catch (e) {
      appendToLast(`\n\n⚠️ Connection error: ${e.message}`);
      setStreaming(false);
    }
  }, [streaming, appendToLast]);

  const clearMessages = useCallback(() => {
    setMessages([]);
    sessionId.current = uuidv4();
  }, []);

  return { messages, streaming, activeTool, sendMessage, clearMessages };
}
