const API_BASE = "http://localhost:8000/api";

export async function fetchSummary() {
  const res = await fetch(`${API_BASE}/dashboard/summary`);
  return res.json();
}

export async function fetchCosts(days = 30) {
  const res = await fetch(`${API_BASE}/costs?days=${days}`);
  return res.json();
}

export async function fetchResources(service?: string) {
  const url = service
    ? `${API_BASE}/resources?service=${service}`
    : `${API_BASE}/resources`;
  const res = await fetch(url);
  return res.json();
}

export async function triggerScan() {
  const res = await fetch(`${API_BASE}/scan`, { method: "POST" });
  return res.json();
}

export async function fetchRecommendations(severity?: string) {
  const url = severity
    ? `${API_BASE}/recommendations?severity=${severity}`
    : `${API_BASE}/recommendations`;
  const res = await fetch(url);
  return res.json();
}

export async function dismissRecommendation(id: number) {
  const res = await fetch(`${API_BASE}/recommendations/${id}?status=dismissed`, {
    method: "PATCH",
  });
  return res.json();
}

export async function* askStream(question: string) {
  const res = await fetch(`${API_BASE}/ask`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question }),
  });

  const reader = res.body?.getReader();
  const decoder = new TextDecoder();
  if (!reader) return;

  let buffer = "";
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop() || "";
    for (const line of lines) {
      if (line.startsWith("data: ")) {
        yield line.slice(6);
      }
    }
  }
}
