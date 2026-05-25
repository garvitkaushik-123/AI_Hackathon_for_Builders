"use client";

import { useEffect, useState, useRef } from "react";
import { fetchRecommendations, dismissRecommendation } from "@/lib/api";
import ChatInterface, { ChatInterfaceHandle } from "@/components/ChatInterface";
import RecommendationCard from "@/components/RecommendationCard";

interface Recommendation {
  id: number;
  resource_id: string | null;
  severity: string;
  title: string;
  description: string;
  estimated_savings: number;
  status: string;
}

export default function AskPage() {
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const chatRef = useRef<ChatInterfaceHandle>(null);

  useEffect(() => {
    fetchRecommendations().then(setRecommendations);
  }, []);

  const handleDismiss = async (id: number) => {
    await dismissRecommendation(id);
    setRecommendations((prev) =>
      prev.map((r) => (r.id === id ? { ...r, status: "dismissed" } : r))
    );
  };

  const handleChat = (question: string) => {
    chatRef.current?.sendMessage(question);
  };

  const activeRecs = recommendations.filter((r) => r.status === "active");

  return (
    <div className="flex gap-6 h-[calc(100vh-8rem)]">
      <div className="flex-1">
        <h1 className="text-2xl font-bold mb-4">AI Assistant</h1>
        <ChatInterface ref={chatRef} />
      </div>
      <div className="w-80 overflow-auto">
        <h2 className="text-lg font-semibold mb-4">
          Recommendations
          {activeRecs.length > 0 && (
            <span className="ml-2 text-sm text-gray-400">({activeRecs.length})</span>
          )}
        </h2>
        {activeRecs.length === 0 ? (
          <p className="text-gray-400 text-sm">
            Looking good! No optimization opportunities found.
          </p>
        ) : (
          <div className="flex flex-col gap-3">
            {activeRecs.map((rec) => (
              <RecommendationCard
                key={rec.id}
                rec={rec}
                onDismiss={handleDismiss}
                onChat={handleChat}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
