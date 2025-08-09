import { api } from "./client";

export interface GenerateReportPayload {
  region_name: string;
  start_date: string;
  end_date: string;
  coordinates: number[][];
}

export async function generateReport(payload: GenerateReportPayload): Promise<Blob> {
  const { data } = await api.post("/generate-report", payload, {
    headers: { "Content-Type": "application/json" },
    responseType: 'blob', // Important: This tells axios to expect a binary response
  });
  return data;
}