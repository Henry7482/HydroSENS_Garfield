import { HydrosensResponse, HydrosensOutputs } from "@/types/hydrosens";

export async function postHydrosens(payload: any): Promise<HydrosensOutputs> {
    return await {
        "2025-05-12": {
            "curve-number": 83.84832182741258,
            ndvi: 0.3225669378328017,
            precipitation: 0,
            "soil-fraction": 0.09270400022385643,
            temperature: 12.416558837890648,
            "vegetation-fraction": 0.6154905115577595,
        },
        "2025-05-13": {
            "curve-number": 83.84832182741258,
            ndvi: 0.3225669378328017,
            precipitation: 0,
            "soil-fraction": 0.09270400022385643,
            temperature: 12.416558837890648,
            "vegetation-fraction": 0.6154905115577595,
        },
    };
}
