export interface HybridData {
  id: string;
  name: string;
  hybridParents: [string, string];
  description: string;
}

export const HYBRIDS: HybridData[] = [
  { id: "hybrid-coywolf", name: "Coywolf", hybridParents: ["M66TP", "QLXJ"],       description: "Eastern Wolf ♂ × Coyote ♀" },
  { id: "hybrid-wolfdog", name: "Wolfdog", hybridParents: ["QLXL", "DOMESTIC_DOG"], description: "Gray Wolf ♂ × Domestic Dog ♀" },
  { id: "hybrid-coydog",  name: "Coydog",  hybridParents: ["QLXJ", "DOMESTIC_DOG"], description: "Coyote ♂ × Domestic Dog ♀" },
];
