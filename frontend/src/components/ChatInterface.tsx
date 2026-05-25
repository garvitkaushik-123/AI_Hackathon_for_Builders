"use client";

import { useState, useRef, useEffect } from "react";
import ReactMarkdown from "react-markdown";
import { askStream } from "@/lib/api";

interface Message {
  role: "user" | "assistant";
  content: string;
}

const SUGGESTED_PROMPTS = [
  "What are my biggest cost saving opportunities?",
  "Why did my bill spike recently?",
  "Which EC2 instances should I downsize?",
  "Predict next month's bill",
  "What would I save with reserved instances?",
];

export default function ChatInterface() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [streaming, setStreaming] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const sendMessage = async (question: string) => {
    if (!question.trim() || streaming) return;

    const userMsg: Message = { role: "user", content: question };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setStreaming(true);

    const assistantMsg: Message = { role: "assistant", content: "" };
    setMessages((prev) => [...prev, assistantMsg]);

    try {
      for await (const chunk of askStream(question)) {
        setMessages((prev) => {
          const updated = [...prev];
          const last = updated[updated.length - 1];
          updated[updated.length - 1] = {
            ...last,
            content: last.content + chunk,
          };
          return updated;
        });
      }
    } catch {
      setMessages((prev) => {
        const updated = [...prev];
        updated[updated.length - 1] = {
          role: "assistant",
          content: "Response interrupted — try again.",
        };
        return updated;
      });
    }

    setStreaming(false);
  };

  return (
    <div className="flex flex-col h-[calc(100vh-10rem)]">
      <div className="flex-1 overflow-auto space-y-4 mb-4 pr-2">
        {messages.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full gap-6">
            <div className="text-center">
              <div className="text-4xl mb-3">&#x1F4AC;</div>
              <p className="text-gray-300 text-lg font-medium">
                Ask anything about your AWS costs
              </p>
              <p className="text-gray-500 text-sm mt-1">
                Get AI-powered insights, predictions, and optimization tips
              </p>
            </div>
            <div className="flex flex-wrap gap-2 justify-center max-w-2xl">
              {SUGGESTED_PROMPTS.map((prompt) => (
                <button
                  key={prompt}
                  onClick={() => sendMessage(prompt)}
                  className="bg-gray-800/80 hover:bg-gray-700 border border-gray-700/50 hover:border-emerald-600/50 text-gray-300 px-4 py-2.5 rounded-xl text-sm transition-all cursor-pointer"
                >
                  {prompt}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((msg, i) => (
          <div
            key={i}
            className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
          >
            {msg.role === "assistant" && (
              <div className="flex-shrink-0 w-8 h-8 rounded-lg bg-emerald-600/20 flex items-center justify-center mr-3 mt-1">
                <span className="text-emerald-400 text-sm">AI</span>
              </div>
            )}
            <div
              className={`max-w-2xl rounded-2xl ${
                msg.role === "user"
                  ? "bg-emerald-600 text-white px-4 py-3 text-sm"
                  : "bg-gray-800/60 border border-gray-700/50 text-gray-200 px-5 py-4"
              }`}
            >
              {msg.role === "assistant" ? (
                <div className="prose-chat">
                  <ReactMarkdown
                    components={{
                      h1: ({ children }) => (
                        <h3 className="text-lg font-bold text-white mt-3 mb-2 first:mt-0">
                          {children}
                        </h3>
                      ),
                      h2: ({ children }) => (
                        <h4 className="text-base font-semibold text-white mt-3 mb-2 first:mt-0">
                          {children}
                        </h4>
                      ),
                      h3: ({ children }) => (
                        <h5 className="text-sm font-semibold text-white mt-2 mb-1 first:mt-0">
                          {children}
                        </h5>
                      ),
                      p: ({ children }) => (
                        <p className="text-sm text-gray-200 leading-relaxed mb-3 last:mb-0">
                          {children}
                        </p>
                      ),
                      strong: ({ children }) => (
                        <strong className="font-semibold text-white">{children}</strong>
                      ),
                      em: ({ children }) => (
                        <em className="text-gray-300 italic">{children}</em>
                      ),
                      ul: ({ children }) => (
                        <ul className="space-y-1.5 mb-3 last:mb-0">{children}</ul>
                      ),
                      ol: ({ children }) => (
                        <ol className="space-y-1.5 mb-3 last:mb-0 list-decimal list-inside">
                          {children}
                        </ol>
                      ),
                      li: ({ children }) => (
                        <li className="text-sm text-gray-200 flex items-start gap-2">
                          <span className="text-emerald-400 mt-1.5 flex-shrink-0 w-1.5 h-1.5 rounded-full bg-emerald-400" />
                          <span className="leading-relaxed">{children}</span>
                        </li>
                      ),
                      code: ({ className, children }) => {
                        const isBlock = className?.includes("language-");
                        if (isBlock) {
                          return (
                            <div className="bg-gray-950 rounded-lg border border-gray-700/50 p-3 my-3 overflow-x-auto">
                              <code className="text-xs text-emerald-300 font-mono">
                                {children}
                              </code>
                            </div>
                          );
                        }
                        return (
                          <code className="bg-gray-900 text-emerald-300 px-1.5 py-0.5 rounded text-xs font-mono">
                            {children}
                          </code>
                        );
                      },
                      pre: ({ children }) => <>{children}</>,
                      table: ({ children }) => (
                        <div className="overflow-x-auto my-3 rounded-lg border border-gray-700/50">
                          <table className="w-full text-sm">{children}</table>
                        </div>
                      ),
                      thead: ({ children }) => (
                        <thead className="bg-gray-900/80">{children}</thead>
                      ),
                      th: ({ children }) => (
                        <th className="text-left px-3 py-2 text-xs font-semibold text-gray-300 border-b border-gray-700/50">
                          {children}
                        </th>
                      ),
                      td: ({ children }) => (
                        <td className="px-3 py-2 text-xs text-gray-300 border-b border-gray-800/50">
                          {children}
                        </td>
                      ),
                      hr: () => <hr className="border-gray-700/50 my-3" />,
                      blockquote: ({ children }) => (
                        <blockquote className="border-l-2 border-emerald-500 pl-3 my-3 text-gray-400 italic">
                          {children}
                        </blockquote>
                      ),
                    }}
                  >
                    {msg.content}
                  </ReactMarkdown>
                  {streaming && i === messages.length - 1 && (
                    <span className="inline-block w-2 h-4 bg-emerald-400 animate-pulse rounded-sm ml-0.5" />
                  )}
                </div>
              ) : (
                <span className="text-sm">{msg.content}</span>
              )}
            </div>
          </div>
        ))}
        <div ref={bottomRef} />
      </div>

      <div className="flex gap-3">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && sendMessage(input)}
          placeholder="Ask about your AWS costs..."
          disabled={streaming}
          className="flex-1 bg-gray-800 border border-gray-700 rounded-xl px-4 py-3 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-emerald-500 transition-colors"
        />
        <button
          onClick={() => sendMessage(input)}
          disabled={streaming || !input.trim()}
          className="bg-emerald-600 hover:bg-emerald-500 disabled:bg-gray-700 disabled:text-gray-500 text-white px-6 py-3 rounded-xl font-medium transition-colors cursor-pointer disabled:cursor-not-allowed"
        >
          {streaming ? (
            <span className="flex items-center gap-2">
              <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
            </span>
          ) : (
            "Send"
          )}
        </button>
      </div>
    </div>
  );
}
