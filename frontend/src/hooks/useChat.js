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
      // Walk backwards to find last assistant message, skipping tool_events
      for (let i = msgs.length - 1; i >= 0; i--) {
        if (msgs[i].role === "assistant") {
          msgs[i] = { ...msgs[i], content: msgs[i].content + text };
          break;
        }
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
              // Store tool event inline so demo mode can render it later
              setMessages(prev => [
                ...prev,
                {
                  type: "tool_event",
                  tool: event.tool,
                  toolUseId: event.tool_use_id,
                  input: event.input,
                  result: null,
                },
              ]);
            } else if (event.type === "tool_result") {
              setActiveTool(null);
              // Fill in result on the matching tool_event
              setMessages(prev => prev.map(msg =>
                msg.type === "tool_event" && msg.toolUseId === event.tool_use_id
                  ? { ...msg, result: event.result }
                  : msg
              ));
            } else if (event.type === "done") {
              setMessages(prev => {
                const msgs = [...prev];
                // Walk backwards to find last assistant message, skipping tool_events
                for (let i = msgs.length - 1; i >= 0; i--) {
                  if (msgs[i].role === "assistant") {
                    msgs[i] = { ...msgs[i], streaming: false };
                    break;
                  }
                }
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
