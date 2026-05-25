"use client";

interface Resource {
  id: number;
  service: string;
  resource_id: string;
  resource_type: string;
  region: string;
  metadata: Record<string, unknown>;
  utilization: Record<string, unknown>;
}

function getUtilColor(cpu: number | undefined): string {
  if (cpu === undefined) return "text-gray-400";
  if (cpu < 5) return "text-red-400";
  if (cpu < 20) return "text-yellow-400";
  return "text-emerald-400";
}

function EC2Table({ resources }: { resources: Resource[] }) {
  return (
    <table className="w-full text-sm">
      <thead>
        <tr className="border-b border-gray-800 text-gray-400">
          <th className="text-left py-3 px-4">Instance ID</th>
          <th className="text-left py-3 px-4">Type</th>
          <th className="text-left py-3 px-4">State</th>
          <th className="text-right py-3 px-4">Avg CPU%</th>
          <th className="text-right py-3 px-4">Network In</th>
          <th className="text-left py-3 px-4">Region</th>
          <th className="text-right py-3 px-4">Est. Cost/mo</th>
        </tr>
      </thead>
      <tbody>
        {resources.map((r) => (
          <tr key={r.id} className="border-b border-gray-800/50 hover:bg-gray-800/30">
            <td className="py-3 px-4 font-mono text-xs">{r.resource_id}</td>
            <td className="py-3 px-4">{r.resource_type}</td>
            <td className="py-3 px-4">{r.metadata.state as string}</td>
            <td className={`py-3 px-4 text-right font-medium ${getUtilColor(r.utilization.avg_cpu_percent as number)}`}>
              {r.utilization.avg_cpu_percent as number}%
            </td>
            <td className="py-3 px-4 text-right">{r.utilization.network_in_gb as number} GB</td>
            <td className="py-3 px-4">{r.region}</td>
            <td className="py-3 px-4 text-right">${r.metadata.monthly_cost as number}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

function RDSTable({ resources }: { resources: Resource[] }) {
  return (
    <table className="w-full text-sm">
      <thead>
        <tr className="border-b border-gray-800 text-gray-400">
          <th className="text-left py-3 px-4">DB ID</th>
          <th className="text-left py-3 px-4">Class</th>
          <th className="text-left py-3 px-4">Engine</th>
          <th className="text-right py-3 px-4">Avg CPU%</th>
          <th className="text-right py-3 px-4">Connections</th>
          <th className="text-left py-3 px-4">Multi-AZ</th>
          <th className="text-right py-3 px-4">Est. Cost/mo</th>
        </tr>
      </thead>
      <tbody>
        {resources.map((r) => (
          <tr key={r.id} className="border-b border-gray-800/50 hover:bg-gray-800/30">
            <td className="py-3 px-4 font-mono text-xs">{r.resource_id}</td>
            <td className="py-3 px-4">{r.resource_type}</td>
            <td className="py-3 px-4">{r.metadata.engine as string}</td>
            <td className={`py-3 px-4 text-right font-medium ${getUtilColor(r.utilization.avg_cpu_percent as number)}`}>
              {r.utilization.avg_cpu_percent as number}%
            </td>
            <td className="py-3 px-4 text-right">{r.utilization.connections as number}</td>
            <td className="py-3 px-4">{(r.metadata.multi_az as boolean) ? "Yes" : "No"}</td>
            <td className="py-3 px-4 text-right">${r.metadata.monthly_cost as number}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

function S3Table({ resources }: { resources: Resource[] }) {
  return (
    <table className="w-full text-sm">
      <thead>
        <tr className="border-b border-gray-800 text-gray-400">
          <th className="text-left py-3 px-4">Bucket Name</th>
          <th className="text-right py-3 px-4">Size (GB)</th>
          <th className="text-right py-3 px-4">Objects</th>
          <th className="text-left py-3 px-4">Storage Class</th>
          <th className="text-right py-3 px-4">Est. Cost/mo</th>
        </tr>
      </thead>
      <tbody>
        {resources.map((r) => (
          <tr key={r.id} className="border-b border-gray-800/50 hover:bg-gray-800/30">
            <td className="py-3 px-4 font-mono text-xs">{r.resource_id}</td>
            <td className="py-3 px-4 text-right">{r.metadata.size_gb as number}</td>
            <td className="py-3 px-4 text-right">{(r.metadata.object_count as number)?.toLocaleString()}</td>
            <td className="py-3 px-4">{r.metadata.storage_class as string}</td>
            <td className="py-3 px-4 text-right">${r.metadata.monthly_cost as number}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

function EBSTable({ resources }: { resources: Resource[] }) {
  return (
    <table className="w-full text-sm">
      <thead>
        <tr className="border-b border-gray-800 text-gray-400">
          <th className="text-left py-3 px-4">Volume ID</th>
          <th className="text-left py-3 px-4">Type</th>
          <th className="text-right py-3 px-4">Size (GB)</th>
          <th className="text-right py-3 px-4">IOPS</th>
          <th className="text-left py-3 px-4">Status</th>
          <th className="text-right py-3 px-4">Est. Cost/mo</th>
        </tr>
      </thead>
      <tbody>
        {resources.map((r) => (
          <tr key={r.id} className="border-b border-gray-800/50 hover:bg-gray-800/30">
            <td className="py-3 px-4 font-mono text-xs">{r.resource_id}</td>
            <td className="py-3 px-4">{r.resource_type}</td>
            <td className="py-3 px-4 text-right">{r.metadata.size_gb as number}</td>
            <td className="py-3 px-4 text-right">{(r.metadata.iops as number)?.toLocaleString()}</td>
            <td className={`py-3 px-4 ${(r.metadata.attached as boolean) ? "text-emerald-400" : "text-red-400"}`}>
              {(r.metadata.attached as boolean) ? "Attached" : "Unattached"}
            </td>
            <td className="py-3 px-4 text-right">${r.metadata.monthly_cost as number}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

const TABLE_MAP: Record<string, React.FC<{ resources: Resource[] }>> = {
  ec2: EC2Table,
  rds: RDSTable,
  s3: S3Table,
  ebs: EBSTable,
};

export default function ResourceTable({
  service,
  resources,
}: {
  service: string;
  resources: Resource[];
}) {
  const Table = TABLE_MAP[service];
  if (!Table) return null;

  if (resources.length === 0) {
    return (
      <div className="bg-gray-900 border border-gray-800 rounded-xl p-12 text-center text-gray-400">
        No {service.toUpperCase()} resources found in this account.
      </div>
    );
  }

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
      <Table resources={resources} />
    </div>
  );
}
