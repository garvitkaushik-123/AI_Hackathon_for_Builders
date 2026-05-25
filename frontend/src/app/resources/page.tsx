"use client";

import { useEffect, useState } from "react";
import { fetchResources } from "@/lib/api";
import ResourceTable from "@/components/ResourceTable";

const TABS = ["ec2", "rds", "s3", "ebs"];

export default function ResourcesPage() {
  const [activeTab, setActiveTab] = useState("ec2");
  const [resources, setResources] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    fetchResources(activeTab).then((data) => {
      setResources(data);
      setLoading(false);
    });
  }, [activeTab]);

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Resources</h1>
      <div className="flex gap-1 mb-6 bg-gray-900 p-1 rounded-lg w-fit">
        {TABS.map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`px-5 py-2 rounded-md font-medium text-sm transition-colors cursor-pointer ${
              activeTab === tab
                ? "bg-emerald-600 text-white"
                : "text-gray-400 hover:text-white"
            }`}
          >
            {tab.toUpperCase()}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="text-gray-400 p-12 text-center">Loading...</div>
      ) : (
        <ResourceTable service={activeTab} resources={resources} />
      )}
    </div>
  );
}
