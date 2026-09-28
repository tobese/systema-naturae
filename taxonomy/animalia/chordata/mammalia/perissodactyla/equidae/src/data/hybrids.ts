export interface HybridData {
  id: string;
  name: string;
  hybridParents: [string, string];
  description: string;
}

// Parent IDs are COL IDs resolved after fetch-taxonomy runs.
// africanus_id = Equus africanus, quagga_id = Equus quagga
export const HYBRIDS: HybridData[] = [
  { id: "hybrid-mule",   name: "Mule",   hybridParents: ["AFRICANUS_ID", "DOMESTIC_HORSE"], description: "Donkey ♂ × Horse ♀" },
  { id: "hybrid-hinny",  name: "Hinny",  hybridParents: ["DOMESTIC_HORSE", "AFRICANUS_ID"], description: "Horse ♂ × Donkey ♀" },
  { id: "hybrid-zorse",  name: "Zorse",  hybridParents: ["QUAGGA_ID",     "DOMESTIC_HORSE"], description: "Zebra ♂ × Horse ♀" },
  { id: "hybrid-zedonk", name: "Zedonk", hybridParents: ["QUAGGA_ID",     "AFRICANUS_ID"],  description: "Zebra ♂ × Donkey ♀" },
];
