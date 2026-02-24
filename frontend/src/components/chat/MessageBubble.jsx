import ReactMarkdown from "react-markdown";

export default function MessageBubble({ message }) {
  const isUser = message.role === "user";

  return (
    <div className={`flex mb-4 ${isUser ? "justify-end" : "justify-start"}`}>
      <div
        className={`max-w-[85%] px-4 py-3 rounded-2xl text-sm leading-relaxed ${
          isUser ? "text-white" : "text-apple-dark"
        }`}
        style={{
          background: isUser ? "#0071E3" : "#FFFFFF",
          border: isUser ? "none" : "1px solid #E5E5EA",
          borderRadius: isUser ? "18px 18px 4px 18px" : "18px 18px 18px 4px",
        }}>
        {isUser ? (
          <p className="whitespace-pre-wrap">{message.content}</p>
        ) : (
          <ReactMarkdown
            components={{
              h2: ({ children }) => <h2 className="font-semibold text-base mt-3 mb-1">{children}</h2>,
              h3: ({ children }) => <h3 className="font-semibold text-sm mt-2 mb-1">{children}</h3>,
              p:  ({ children }) => <p className="mb-2 last:mb-0">{children}</p>,
              ul: ({ children }) => <ul className="list-disc list-inside space-y-1 mb-2">{children}</ul>,
              ol: ({ children }) => <ol className="list-decimal list-inside space-y-1 mb-2">{children}</ol>,
              li: ({ children }) => <li className="text-sm">{children}</li>,
              strong: ({ children }) => <strong className="font-semibold">{children}</strong>,
              hr: () => <hr className="my-3 border-gray-200" />,
              code: ({ children }) => <code className="bg-gray-100 px-1.5 py-0.5 rounded text-xs font-mono">{children}</code>,
            }}>
            {message.content || (message.streaming ? "▋" : "")}
          </ReactMarkdown>
        )}
      </div>
    </div>
  );
}
