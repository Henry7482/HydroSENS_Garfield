import { HydrosensResponse, HydrosensOutputs } from "@/types/hydrosens";
import { api } from "./client";

export async function postHydrosens(payload: any): Promise<HydrosensOutputs> {
    const { data } = await api.post<HydrosensResponse>("/analyze", payload, {
        headers: { "Content-Type": "application/json" },
    });
    return data.outputs;
}
