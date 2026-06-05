import type { ClaimSubmitRequest, ClaimResponse, DocumentField } from "../types";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

export async function submitClaim(data: ClaimSubmitRequest): Promise<ClaimResponse> {
  const res = await fetch(`${API_URL}/api/claims`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const err = await res.text();
    throw new Error(err || `HTTP ${res.status}`);
  }
  return res.json();
}

export async function getClaim(id: string): Promise<ClaimResponse> {
  const res = await fetch(`${API_URL}/api/claims/${id}`);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

export async function processDocument(file: File): Promise<DocumentField> {
  const body = new FormData();
  body.append("file", file);
  const res = await fetch(`${API_URL}/api/documents/process`, {
    method: "POST",
    body,
  });
  if (!res.ok) {
    const err = await res.text();
    throw new Error(err || `HTTP ${res.status}`);
  }
  return res.json();
}
