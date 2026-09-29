export interface HybridData {
  id: string;
  name: string;
  hybridParents: [string, string];
  description: string;
}

export const HYBRIDS: HybridData[] = [
  { id: "hybrid-liger",   name: "Liger",   hybridParents: ["4CGXP", "4CGXS"], description: "Lion ♂ × Tiger ♀" },
  { id: "hybrid-tigon",   name: "Tigon",   hybridParents: ["4CGXS", "4CGXP"], description: "Tiger ♂ × Lion ♀" },
  { id: "hybrid-leopon",  name: "Leopon",  hybridParents: ["4CGXR", "4CGXP"], description: "Leopard ♂ × Lion ♀" },
  { id: "hybrid-caraval", name: "Caraval", hybridParents: ["QZRR",  "3THH7"], description: "Caracal ♂ × Serval ♀" },
  { id: "hybrid-jagulep", name: "Jagulep", hybridParents: ["4CGXQ", "4CGXR"], description: "Jaguar ♂ × Leopard ♀" },
  { id: "hybrid-pumapard",name: "Pumapard",hybridParents: ["4QHKG", "4CGXR"], description: "Puma ♂ × Leopard ♀" },
];
