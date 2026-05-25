"use client";

import { useEffect, useState } from "react";
import { fetchAWSStatus, connectAWS, disconnectAWS } from "@/lib/api";

type AWSStatus = {
  connected: boolean;
  source: string | null;
  region: string | null;
  account_id: string | null;
  iam_user: string | null;
};

const IAM_POLICY = `{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "CloudOptReadOnly",
      "Effect": "Allow",
      "Action": [
        "ec2:DescribeInstances",
        "ec2:DescribeVolumes",
        "rds:DescribeDBInstances",
        "s3:ListAllMyBuckets",
        "s3:GetBucketLocation",
        "cloudwatch:GetMetricStatistics",
        "ce:GetCostAndUsage",
        "sts:GetCallerIdentity"
      ],
      "Resource": "*"
    }
  ]
}`;

const SETUP_STEPS = [
  {
    step: 1,
    title: "Create an IAM User",
    detail:
      'Go to AWS Console > IAM > Users > "Create user". Name it cloudopt-readonly. Do NOT enable console access.',
  },
  {
    step: 2,
    title: "Attach the Read-Only Policy",
    detail:
      'Choose "Attach policies directly", click "Create policy", switch to JSON tab, and paste the policy shown below.',
  },
  {
    step: 3,
    title: "Create Access Keys",
    detail:
      'Select the user > Security credentials > "Create access key". Choose "Third-party service". Copy both the Access Key ID and Secret Access Key.',
  },
  {
    step: 4,
    title: "Enter Credentials Below",
    detail:
      "Paste the Access Key ID and Secret Access Key into the form below. We validate them with STS before saving.",
  },
];

export default function SettingsPage() {
  const [status, setStatus] = useState<AWSStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [connecting, setConnecting] = useState(false);
  const [error, setError] = useState("");
  const [showGuide, setShowGuide] = useState(true);

  const [accessKeyId, setAccessKeyId] = useState("");
  const [secretAccessKey, setSecretAccessKey] = useState("");
  const [region, setRegion] = useState("ap-south-1");

  const loadStatus = async () => {
    try {
      const data = await fetchAWSStatus();
      setStatus(data);
    } catch {
      setStatus({ connected: false, source: null, region: null, account_id: null, iam_user: null });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadStatus();
  }, []);

  const handleConnect = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setConnecting(true);
    try {
      await connectAWS({
        access_key_id: accessKeyId,
        secret_access_key: secretAccessKey,
        region,
      });
      setAccessKeyId("");
      setSecretAccessKey("");
      await loadStatus();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Connection failed");
    } finally {
      setConnecting(false);
    }
  };

  const handleDisconnect = async () => {
    await disconnectAWS();
    await loadStatus();
  };

  const [copied, setCopied] = useState(false);
  const copyPolicy = () => {
    navigator.clipboard.writeText(IAM_POLICY);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  if (loading) {
    return (
      <div className="text-gray-400 p-12 text-center">Loading settings...</div>
    );
  }

  const isConnected = status?.connected;

  return (
    <div className="max-w-3xl">
      <h1 className="text-2xl font-bold mb-6">Settings</h1>

      {/* Data Mode Banner */}
      <div
        className={`rounded-xl border p-4 mb-6 flex items-center gap-4 ${
          isConnected
            ? "bg-emerald-900/20 border-emerald-700/50"
            : "bg-amber-900/20 border-amber-700/50"
        }`}
      >
        <div
          className={`flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center text-lg ${
            isConnected ? "bg-emerald-600/20" : "bg-amber-600/20"
          }`}
        >
          {isConnected ? "✅" : "⚠️"}
        </div>
        <div>
          {isConnected ? (
            <>
              <p className="text-emerald-400 font-medium">Live AWS Data</p>
              <p className="text-gray-400 text-sm">
                Connected to AWS account{" "}
                {status?.account_id && (
                  <span className="font-mono text-gray-300">{status.account_id}</span>
                )}{" "}
                via {status?.source === "ui" ? "dashboard credentials" : "environment variables"}.
                Scans pull real infrastructure data.
              </p>
            </>
          ) : (
            <>
              <p className="text-amber-400 font-medium">Using Mock Data</p>
              <p className="text-gray-400 text-sm">
                No AWS credentials configured. The platform is running with
                simulated data. Connect your AWS account below to scan real
                infrastructure.
              </p>
            </>
          )}
        </div>
      </div>

      {/* Connection Status (when connected) */}
      {isConnected && (
        <div className="bg-gray-900 rounded-xl border border-gray-800 p-6 mb-6">
          <h2 className="text-lg font-semibold mb-4">AWS Connection</h2>
          <div className="flex items-center gap-3 mb-4">
            <span className="w-3 h-3 rounded-full bg-emerald-400 animate-pulse" />
            <span className="text-emerald-400 font-medium">Connected</span>
          </div>

          <div className="grid grid-cols-3 gap-4 text-sm mb-6">
            {status?.account_id && (
              <div>
                <span className="text-gray-500">Account ID</span>
                <p className="text-white font-mono">{status.account_id}</p>
              </div>
            )}
            {status?.iam_user && (
              <div>
                <span className="text-gray-500">IAM User</span>
                <p className="text-white font-mono">{status.iam_user}</p>
              </div>
            )}
            {status?.region && (
              <div>
                <span className="text-gray-500">Region</span>
                <p className="text-white font-mono">{status.region}</p>
              </div>
            )}
          </div>

          {status?.source === "ui" && (
            <button
              onClick={handleDisconnect}
              className="px-4 py-2 rounded-lg bg-red-600/20 text-red-400 hover:bg-red-600/30 transition-colors text-sm cursor-pointer"
            >
              Disconnect & Switch to Mock Data
            </button>
          )}
          {status?.source === "env" && (
            <p className="text-gray-500 text-sm">
              Connected via environment variables. Remove AWS_ACCESS_KEY_ID and
              AWS_SECRET_ACCESS_KEY from your .env file to disconnect.
            </p>
          )}
        </div>
      )}

      {/* Credential Form — always visible when not connected */}
      <div className="bg-gray-900 rounded-xl border border-gray-800 p-6 mb-6">
        <h2 className="text-lg font-semibold mb-2">
          {isConnected ? "Update AWS Credentials" : "Connect AWS Account"}
        </h2>
        <p className="text-gray-500 text-sm mb-4">
          {isConnected
            ? "Replace the current credentials with new ones."
            : "Enter your IAM access keys to switch from mock data to live AWS scanning."}
        </p>
        <form onSubmit={handleConnect} className="space-y-4">
          <div>
            <label className="block text-sm text-gray-400 mb-1">
              Access Key ID
            </label>
            <input
              type="text"
              value={accessKeyId}
              onChange={(e) => setAccessKeyId(e.target.value)}
              placeholder="AKIA..."
              required
              className="w-full bg-gray-950 border border-gray-700 rounded-lg px-4 py-2.5 text-white placeholder-gray-600 focus:outline-none focus:border-emerald-500 font-mono text-sm"
            />
          </div>
          <div>
            <label className="block text-sm text-gray-400 mb-1">
              Secret Access Key
            </label>
            <input
              type="password"
              value={secretAccessKey}
              onChange={(e) => setSecretAccessKey(e.target.value)}
              placeholder="wJalr..."
              required
              className="w-full bg-gray-950 border border-gray-700 rounded-lg px-4 py-2.5 text-white placeholder-gray-600 focus:outline-none focus:border-emerald-500 font-mono text-sm"
            />
          </div>
          <div>
            <label className="block text-sm text-gray-400 mb-1">Region</label>
            <select
              value={region}
              onChange={(e) => setRegion(e.target.value)}
              className="w-full bg-gray-950 border border-gray-700 rounded-lg px-4 py-2.5 text-white focus:outline-none focus:border-emerald-500 text-sm"
            >
              <option value="ap-south-1">Asia Pacific (Mumbai)</option>
              <option value="us-east-1">US East (N. Virginia)</option>
              <option value="us-east-2">US East (Ohio)</option>
              <option value="us-west-1">US West (N. California)</option>
              <option value="us-west-2">US West (Oregon)</option>
              <option value="eu-west-1">EU (Ireland)</option>
              <option value="eu-central-1">EU (Frankfurt)</option>
              <option value="ap-southeast-1">Asia Pacific (Singapore)</option>
              <option value="ap-northeast-1">Asia Pacific (Tokyo)</option>
            </select>
          </div>

          {error && (
            <div className="bg-red-600/10 border border-red-600/30 text-red-400 rounded-lg px-4 py-3 text-sm">
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={connecting}
            className="w-full bg-emerald-600 hover:bg-emerald-500 disabled:bg-gray-700 disabled:text-gray-500 text-white font-medium py-2.5 rounded-lg transition-colors cursor-pointer"
          >
            {connecting ? "Validating..." : "Connect & Validate"}
          </button>

          <p className="text-gray-600 text-xs text-center">
            Credentials are validated with AWS STS and stored locally. Only
            read-only API calls are made.
          </p>
        </form>
      </div>

      {/* IAM Setup Guide — always visible */}
      <div className="bg-gray-900 rounded-xl border border-gray-800 p-6">
        <button
          onClick={() => setShowGuide(!showGuide)}
          className="flex items-center justify-between w-full text-left cursor-pointer"
        >
          <h2 className="text-lg font-semibold">IAM Setup Guide</h2>
          <span className="text-gray-500 text-xl">
            {showGuide ? "−" : "+"}
          </span>
        </button>

        {showGuide && (
          <div className="mt-4 space-y-4">
            {SETUP_STEPS.map((s) => (
              <div key={s.step} className="flex gap-4">
                <div className="flex-shrink-0 w-8 h-8 rounded-full bg-emerald-600/20 text-emerald-400 flex items-center justify-center text-sm font-bold">
                  {s.step}
                </div>
                <div>
                  <h3 className="font-medium text-white">{s.title}</h3>
                  <p className="text-gray-400 text-sm mt-1">{s.detail}</p>
                </div>
              </div>
            ))}

            {/* IAM Policy Block */}
            <div className="mt-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm text-gray-400 font-medium">
                  IAM Policy (JSON)
                </span>
                <button
                  onClick={copyPolicy}
                  className="text-xs text-emerald-400 hover:text-emerald-300 cursor-pointer"
                >
                  {copied ? "Copied!" : "Copy"}
                </button>
              </div>
              <pre className="bg-gray-950 border border-gray-800 rounded-lg p-4 text-xs text-gray-300 overflow-x-auto">
                {IAM_POLICY}
              </pre>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
