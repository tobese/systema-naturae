/**
 * Bootstrap 8 remaining animal phyla into the portal.
 *
 * Classification (option B — real scientific):
 *
 *   Phoronida         → Class Phoronida     → Order Phoronida
 *   Loricifera        → Class Loricifera    → Order Nanaloricida
 *   Priapulida        → Class Priapulimorpha|Halicryptomorpha|Seticoronaria
 *   Entoprocta        → Class Entoprocta    → Order Solitaria|Coloniales
 *   Gnathostomulida   → Class Gnathostomulida → Order Filospermoidea|Bursovaginoidea
 *   Onychophora       → Class Onychophora   → Order Euonychophora
 *   Gastrotricha      → Class Gastrotricha  → Order Chaetonotida|Macrodasyida
 *   Xenacoelomorpha   → Class Xenoturbellida|Acoela|Nemertodermatida
 *
 * Usage: npx tsx scripts/bootstrapAnimalPhyla.ts
 */

import { writeFileSync, mkdirSync } from "fs";
import { resolve, dirname } from "path";
import { fileURLToPath } from "url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const root = resolve(__dirname, "..");

// ── Classification config ──
interface ClassDef {
  id: string;
  name: string;
  orders: OrderDef[];
}
interface OrderDef {
  id: string;
  name: string;
  families: FamilyDef[];
}
interface FamilyDef {
  name: string;
  gbifKey: number;
}

const PHYLA: Record<string, { phylumId: string; commonName: string; classes: ClassDef[] }> = {
  phoronida: {
    phylumId: "PHORONIDA",
    commonName: "Horseshoe worms",
    classes: [{
      id: "CLS_PHORONIDA",
      name: "Phoronida",
      orders: [{
        id: "ORD_PHORONIDA",
        name: "Phoronida",
        families: [{ name: "Phoronidae", gbifKey: 3237816 }],
      }],
    }],
  },
  loricifera: {
    phylumId: "LORICIFERA",
    commonName: "Brush heads",
    classes: [{
      id: "CLS_LORICIFERA",
      name: "Loricifera",
      orders: [{
        id: "ORD_NANALORICIDA",
        name: "Nanaloricida",
        families: [
          { name: "Nanaloricidae", gbifKey: 1990 },
          { name: "Pliciloricidae", gbifKey: 1991 },
          { name: "Urnaloricidae", gbifKey: 6472449 },
        ],
      }],
    }],
  },
  priapulida: {
    phylumId: "PRIAPULIDA",
    commonName: "Penis worms",
    classes: [
      {
        id: "CLS_PRIAPULIMORPHA",
        name: "Priapulimorpha",
        orders: [
          {
            id: "ORD_PRIAPULOMORPHA",
            name: "Priapulomorpha",
            families: [{ name: "Priapulidae", gbifKey: 5974 }],
          },
          {
            id: "ORD_MEIOPRIAPULOMORPHA",
            name: "Meiopriapulomorpha",
            families: [{ name: "Meiopriapulidae", gbifKey: 8453914 }],
          },
        ],
      },
      {
        id: "CLS_HALICRYPTOMORPHA",
        name: "Halicryptomorpha",
        orders: [{
          id: "ORD_HALICRYPTOMORPHA",
          name: "Halicryptomorpha",
          families: [{ name: "Halicryptidae", gbifKey: 9247 }],
        }],
      },
      {
        id: "CLS_SETICORONARIA",
        name: "Seticoronaria",
        orders: [{
          id: "ORD_SETICORONARIA",
          name: "Seticoronaria",
          families: [{ name: "Chaetostephanidae", gbifKey: 6126 }],
        }],
      },
    ],
  },
  entoprocta: {
    phylumId: "ENTOPROCTA",
    commonName: "Goblet worms",
    classes: [{
      id: "CLS_ENTOPROCTA",
      name: "Entoprocta",
      orders: [
        {
          id: "ORD_SOLITARIA",
          name: "Solitaria",
          families: [
            { name: "Loxokalypodidae", gbifKey: 5854 },
            { name: "Barentsiidae", gbifKey: 5853 },
            { name: "Pedicellinidae", gbifKey: 5855 },
          ],
        },
        {
          id: "ORD_COLONIALES",
          name: "Coloniales",
          families: [
            { name: "Loxosomatidae", gbifKey: 5852 },
          ],
        },
      ],
    }],
  },
  gnathostomulida: {
    phylumId: "GNATHOSTOMULIDA",
    commonName: "Jaw worms",
    classes: [{
      id: "CLS_GNATHOSTOMULIDA",
      name: "Gnathostomulida",
      orders: [
        {
          id: "ORD_FILOSPERMOIDEA",
          name: "Filospermoidea",
          families: [
            { name: "Haplognathiidae", gbifKey: 1974 },
            { name: "Pterognathiidae", gbifKey: 9173 },
          ],
        },
        {
          id: "ORD_BURSOVAGINOIDEA",
          name: "Bursovaginoidea",
          families: [
            { name: "Agnathiellidae", gbifKey: 1979 },
            { name: "Austrognathiidae", gbifKey: 1976 },
            { name: "Clausognathiidae", gbifKey: 6483672 },
            { name: "Gnathostomariidae", gbifKey: 5059 },
            { name: "Gnathostomulidae", gbifKey: 1973 },
            { name: "Mesognathariidae", gbifKey: 1977 },
            { name: "Onychognathiidae", gbifKey: 1975 },
            { name: "Paucidentulidae", gbifKey: 8830333 },
            { name: "Problognathiidae", gbifKey: 1978 },
            { name: "Rastrognathiidae", gbifKey: 2743 },
          ],
        },
      ],
    }],
  },
  onychophora: {
    phylumId: "ONYCHOPHORA",
    commonName: "Velvet worms",
    classes: [{
      id: "CLS_ONYCHOPHORA",
      name: "Onychophora",
      orders: [{
        id: "ORD_EUONYCHOPHORA",
        name: "Euonychophora",
        families: [
          { name: "Peripatidae", gbifKey: 1899 },
          { name: "Peripatopsidae", gbifKey: 1898 },
        ],
      }],
    }],
  },
  gastrotricha: {
    phylumId: "GASTROTRICHA",
    commonName: "Hairy backs",
    classes: [{
      id: "CLS_GASTROTRICHA",
      name: "Gastrotricha",
      orders: [
        {
          id: "ORD_CHAETONOTIDA",
          name: "Chaetonotida",
          families: [
            { name: "Chaetonotidae", gbifKey: 7393 },
            { name: "Dasydytidae", gbifKey: 3429 },
            { name: "Dichaeturidae", gbifKey: 7392 },
            { name: "Neogosseidae", gbifKey: 3426 },
            { name: "Proichthydiidae", gbifKey: 7389 },
            { name: "Xenotrichulidae", gbifKey: 7387 },
            { name: "Muselliferidae", gbifKey: 4351251 },
          ],
        },
        {
          id: "ORD_MACRODASYIDA",
          name: "Macrodasyida",
          families: [
            { name: "Cephalodasyidae", gbifKey: 7921774 },
            { name: "Dactylopodolidae", gbifKey: 3430 },
            { name: "Hummondasyidae", gbifKey: 8247597 },
            { name: "Lepidodasyidae", gbifKey: 7391 },
            { name: "Macrodasyidae", gbifKey: 3428 },
            { name: "Neodasyidae", gbifKey: 3427 },
            { name: "Planodasyidae", gbifKey: 7390 },
            { name: "Redudasyidae", gbifKey: 8229258 },
            { name: "Thaumastodermatidae", gbifKey: 7388 },
            { name: "Turbanellidae", gbifKey: 3425 },
            { name: "Xenodasyidae", gbifKey: 3424 },
          ],
        },
      ],
    }],
  },
  xenacoelomorpha: {
    phylumId: "XENACOELOMORPHA",
    commonName: "Xenacoelomorphs",
    classes: [
      {
        id: "CLS_XENOTURBELLIDA",
        name: "Xenoturbellida",
        orders: [{
          id: "ORD_XENOTURBELLIDA",
          name: "Xenoturbellida",
          families: [
            { name: "Xenoturbellidae", gbifKey: 5396 },
          ],
        }],
      },
      {
        id: "CLS_ACOELA",
        name: "Acoela",
        orders: [{
          id: "ORD_ACOELA",
          name: "Acoela",
          families: [
            { name: "Actinoposthiidae", gbifKey: 6251 },
            { name: "Antigonariidae", gbifKey: 6267 },
            { name: "Antroposthiidae", gbifKey: 6262 },
            { name: "Convolutidae", gbifKey: 6265 },
            { name: "Dakuidae", gbifKey: 6471361 },
            { name: "Diopisthoporidae", gbifKey: 6260 },
            { name: "Hallangiidae", gbifKey: 7951330 },
            { name: "Hofsteniidae", gbifKey: 6266 },
            { name: "Isodiametridae", gbifKey: 6261 },
            { name: "Mecynostomidae", gbifKey: 6264 },
            { name: "Nadinidae", gbifKey: 4551543 },
            { name: "Otocelididae", gbifKey: 6268 },
            { name: "Paratomellidae", gbifKey: 6471362 },
            { name: "Proporidae", gbifKey: 6259 },
            { name: "Sagittiferidae", gbifKey: 6263 },
            { name: "Solenofilomorphidae", gbifKey: 6257 },
            { name: "Taurididae", gbifKey: 6471360 },
          ],
        }],
      },
      {
        id: "CLS_NEMERTODERMATIDA",
        name: "Nemertodermatida",
        orders: [{
          id: "ORD_NEMERTODERMATIDA",
          name: "Nemertodermatida",
          families: [
            { name: "Ascopariidae", gbifKey: 6471371 },
            { name: "Nemertodermatidae", gbifKey: 1993 },
          ],
        }],
      },
    ],
  },
};

const PHYLUM_ORDER = [
  "phoronida",
  "loricifera",
  "priapulida",
  "entoprocta",
  "gnathostomulida",
  "onychophora",
  "gastrotricha",
  "xenacoelomorpha",
];

// ── Id helpers ──
function famId(name: string): string {
  const base = name.replace(/idae$/i, "").toUpperCase();
  return `FAM_${base}IDAE`;
}
function genusId(name: string): string {
  return `GENUS_${name.toUpperCase()}`;
}
function spId(name: string): string {
  return name.replace(/[^a-zA-Z0-9]/g, "_").toUpperCase();
}

// ── Fetch species from GBIF ──
async function fetchFamilySpecies(familyKey: number): Promise<any[]> {
  const species: any[] = [];
  let offset = 0;
  const limit = 300;
  while (true) {
    const url = `https://api.gbif.org/v1/species/search?higherTaxonKey=${familyKey}&rank=SPECIES&status=ACCEPTED&limit=${limit}&offset=${offset}`;
    const resp = await fetch(url);
    if (!resp.ok) {
      console.warn(`  GBIF error ${resp.status} for family ${familyKey}, offset ${offset}`);
      break;
    }
    const data = await resp.json();
    species.push(...data.results);
    if (data.results.length < limit) break;
    offset += limit;
  }
  return species;
}

function buildFamilyJson(familyName: string, species: any[]): any {
  const slug = familyName.toLowerCase();
  const genusMap = new Map<string, any[]>();

  for (const sp of species) {
    const genus = sp.genus || "Unknown";
    if (!genusMap.has(genus)) genusMap.set(genus, []);
    genusMap.get(genus)!.push(sp);
  }

  const children: any[] = [];
  const genusEntries = [...genusMap.entries()].sort((a, b) => a[0].localeCompare(b[0]));

  for (const [genus, spp] of genusEntries) {
    const spChildren = spp.map(sp => ({
      id: spId(sp.species || sp.canonicalName),
      name: sp.species || sp.canonicalName,
      rank: "SPECIES",
      lineage: genus,
      continents: [],
      subspeciesCount: 0,
      description: `${sp.species} — a species of ${genus} in the family ${familyName}.`,
      sourcedFrom: "gbif",
    }));

    children.push({
      id: genusId(genus),
      name: genus,
      rank: "GENUS",
      description: `${genus} — a genus in the family ${familyName}.`,
      lineage: genus,
      children: spChildren,
    });
  }

  return {
    id: famId(familyName),
    name: familyName,
    rank: "FAMILY",
    commonName: familyName.replace("idae", "ids"),
    children,
  };
}

// ── Write data files ──
function writeFamilyData(phylum: string, cls: string, order: string, familyJson: any): void {
  const slug = familyJson.name.toLowerCase();
  const dir = resolve(root, phylum, cls.toLowerCase(), order.toLowerCase(), slug, "src", "data");
  const filePath = resolve(dir, `${slug}.json`);
  mkdirSync(dir, { recursive: true });
  writeFileSync(filePath, JSON.stringify(familyJson, null, 2));
  console.log(`  Wrote ${filePath}`);
}

// ── Main ──
async function main() {
  console.log("Bootstrapping 8 animal phyla...\n");

  // Collect family species counts for taxonomy snippet
  const familyCounts = new Map<string, number>();

  let taxonomyInsertions: string[] = [];
  let colorEntries: string[] = [];

  for (const pSlug of PHYLUM_ORDER) {
    const phylum = PHYLA[pSlug];

    console.log(`\n=== ${phylum.phylumId} (${phylum.commonName}) ===`);

    for (const cls of phylum.classes) {
      for (const ord of cls.orders) {
        for (const fam of ord.families) {
          console.log(`  Fetching ${fam.name} (key ${fam.gbifKey})...`);
          const species = await fetchFamilySpecies(fam.gbifKey);

          console.log(`    → ${species.length} accepted species`);
          familyCounts.set(fam.name.toLowerCase(), species.length);

          const famJson = buildFamilyJson(fam.name, species);
          writeFamilyData(pSlug, cls.name, ord.name, famJson);

          // Generate color theme — derived from phylum name for consistency
          let hash = 0;
          for (let i = 0; i < pSlug.length; i++) {
            hash = pSlug.charCodeAt(i) + ((hash << 5) - hash);
          }
          const hue = ((hash % 360) + 360) % 360;
          const colorName = `${fam.name.toUpperCase().replace(/[^A-Z0-9]/g, "_")}_THEME`;

          colorEntries.push(`const ${colorName}: ColorTheme = {
  accent: "hsl(${hue}, 35%, 50%)",
  accentDim: "hsl(${hue}, 25%, 35%)",
  accentMuted: "hsl(${hue}, 20%, 20%)",
  accentBg: "hsl(${hue}, 15%, 12%)",
  accentBgMuted: "hsl(${hue}, 10%, 9%)",
  accentOnAccent: "#fff",
};
`);

          colorEntries.push(`"${fam.name.toLowerCase()}": ${colorName},`);
        }
      }
    }

    // ── Generate taxonomy.json snippet ──
    function cap(s: string): string {
      return s.charAt(0).toUpperCase() + s.slice(1).toLowerCase();
    }

    function phylumName(id: string): string {
      return id.charAt(0) + id.slice(1).toLowerCase();
    }

    let snippet = `    {
      "id": "${phylum.phylumId}",
      "name": "${phylumName(phylum.phylumId)}",
      "rank": "PHYLUM",
      "commonName": "${phylum.commonName}",
      "children": [\n`;

    for (const cls of phylum.classes) {
      snippet += `        {
          "id": "${cls.id}",
          "name": "${cls.name}",
          "rank": "CLASS",
          "children": [\n`;

      for (const ord of cls.orders) {
        snippet += `            {
              "id": "${ord.id}",
              "name": "${ord.name}",
              "rank": "ORDER",
              "children": [\n`;

        for (const fam of ord.families) {
          const count = familyCounts.get(fam.name.toLowerCase()) || 0;
          snippet += `                {
                  "id": "${famId(fam.name)}",
                  "name": "${fam.name}",
                  "rank": "FAMILY",
                  "commonName": "${fam.name.replace("idae", "ids")}",
                  "appSlug": "${fam.name.toLowerCase()}",
                  "speciesCount": ${count}
                },\n`;
        }

        snippet += `              ]
            },\n`;
      }

      snippet += `          ]
        },\n`;
    }

    snippet += `      ]
    },`;
    taxonomyInsertions.push(snippet);
  }

  // ── Write outputs ──
  const outDir = resolve(root, "scripts", "output");
  mkdirSync(outDir, { recursive: true });

  const taxPath = resolve(outDir, "taxonomy-snippets.json");
  writeFileSync(taxPath, taxonomyInsertions.join("\n\n"));
  console.log(`\n\nTaxonomy snippets → ${taxPath}`);

  const colorPath = resolve(outDir, "color-registry-entries.txt");
  writeFileSync(colorPath, colorEntries.join("\n"));
  console.log(`Color entries → ${colorPath}`);

  console.log("\nDone! 8 phyla bootstrapped.");
  console.log("\nManual steps remaining:");
  console.log("  1. Merge taxonomy snippets into portal/data/taxonomy.json (insert after Tardigrada block)");
  console.log("  2. Merge color entries into portal/src/colorRegistry.ts");
  console.log("  3. Update speciesCount in taxonomy.json for each family (from the GBIF output above)");
  console.log("  4. Rebuild: cd portal && sh scripts/buildData.sh");
  console.log("  5. Check pending-eponyms.json for any eponym species to add");
}

main().catch(console.error);
