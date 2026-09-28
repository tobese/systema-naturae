import { writeFileSync } from "fs";
import { join } from "path";
import * as topojson from "topojson-client";
import worldTopo from "world-atlas/countries-110m.json" assert { type: "json" };
import type { Topology, GeometryCollection } from "topojson-specification";

// ISO numeric country IDs → continent name
// Source: UN M.49 standard groupings
const ISO_TO_CONTINENT: Record<number, string> = {
  // Africa
  12: "Africa", 24: "Africa", 72: "Africa", 86: "Africa", 108: "Africa",
  120: "Africa", 132: "Africa", 140: "Africa", 148: "Africa", 174: "Africa",
  175: "Africa", 178: "Africa", 180: "Africa", 204: "Africa", 218: "Africa",
  226: "Africa", 231: "Africa", 232: "Africa", 260: "Africa", 266: "Africa",
  270: "Africa", 288: "Africa", 324: "Africa", 384: "Africa", 404: "Africa",
  426: "Africa", 430: "Africa", 434: "Africa", 450: "Africa", 454: "Africa",
  466: "Africa", 478: "Africa", 480: "Africa", 504: "Africa", 508: "Africa",
  516: "Africa", 562: "Africa", 566: "Africa", 585: "Africa", 626: "Africa",
  646: "Africa", 678: "Africa", 686: "Africa", 694: "Africa", 706: "Africa",
  710: "Africa", 716: "Africa", 728: "Africa", 729: "Africa", 768: "Africa",
  788: "Africa", 800: "Africa", 818: "Africa", 834: "Africa", 894: "Africa",
  938: "Africa", 896: "Africa",

  // Asia
  4: "Asia", 50: "Asia", 64: "Asia", 96: "Asia", 104: "Asia",
  116: "Asia", 144: "Asia", 156: "Asia", 162: "Asia", 356: "Asia",
  360: "Asia", 364: "Asia", 368: "Asia", 376: "Asia", 392: "Asia",
  400: "Asia", 408: "Asia", 410: "Asia", 414: "Asia", 417: "Asia",
  418: "Asia", 422: "Asia", 458: "Asia", 462: "Asia", 496: "Asia",
  524: "Asia", 512: "Asia", 586: "Asia", 608: "Asia", 634: "Asia",
  682: "Asia", 703: "Asia", 702: "Asia", 760: "Asia", 762: "Asia",
  764: "Asia", 792: "Asia", 795: "Asia", 784: "Asia", 860: "Asia",
  704: "Asia", 887: "Asia", 158: "Asia", 344: "Asia", 446: "Asia",
  275: "Asia", 51: "Asia", 31: "Asia",

  // Europe
  8: "Europe", 20: "Europe", 40: "Europe", 56: "Europe", 70: "Europe",
  100: "Europe", 112: "Europe", 191: "Europe", 196: "Europe", 203: "Europe",
  208: "Europe", 233: "Europe", 246: "Europe", 250: "Europe", 276: "Europe",
  300: "Europe", 336: "Europe", 348: "Europe", 352: "Europe", 372: "Europe",
  380: "Europe", 428: "Europe", 438: "Europe", 440: "Europe", 442: "Europe",
  470: "Europe", 492: "Europe", 498: "Europe", 499: "Europe", 528: "Europe",
  578: "Europe", 616: "Europe", 620: "Europe", 642: "Europe", 643: "Europe",
  674: "Europe", 688: "Europe", 703: "Europe", 705: "Europe", 724: "Europe",
  744: "Europe", 752: "Europe", 756: "Europe", 804: "Europe", 807: "Europe",
  826: "Europe", 831: "Europe", 832: "Europe", 833: "Europe",

  // North America
  28: "North America", 44: "North America", 52: "North America",
  84: "North America", 124: "North America", 136: "North America",
  170: "North America", 188: "North America", 192: "North America",
  212: "North America", 214: "North America", 222: "North America",
  308: "North America", 320: "North America", 332: "North America",
  340: "North America", 388: "North America", 484: "North America",
  558: "North America", 591: "North America", 630: "North America",
  659: "North America", 660: "North America", 662: "North America",
  663: "North America", 670: "North America", 780: "North America",
  796: "North America", 840: "North America",

  // South America
  32: "South America", 68: "South America", 76: "South America",
  152: "South America", 170: "South America", 218: "South America",
  238: "South America", 254: "South America", 328: "South America",
  332: "South America", 600: "South America", 604: "South America",
  740: "South America", 858: "South America", 862: "South America",

  // Oceania (excluded from our 5 continents — skip)
};

// Fix duplicates between South America and other regions (Colombia, Ecuador are SA not NA)
const OVERRIDES: Record<number, string> = {
  170: "South America", // Colombia
  218: "South America", // Ecuador
  332: "South America", // Haiti — actually Caribbean/North America
};

const CONTINENT_NAMES = ["Africa", "Asia", "Europe", "North America", "South America"] as const;

const CONTINENT_COLORS: Record<string, string> = {
  "Africa":        "#C87941",
  "Asia":          "#2E9E8C",
  "Europe":        "#5B8DD9",
  "North America": "#7B6FA0",
  "South America": "#E05C5C",
};

const topo = worldTopo as unknown as Topology<{ countries: GeometryCollection }>;

const allGeoms = topo.objects.countries.geometries;

const features = CONTINENT_NAMES.map(continentName => {
  const geoms = allGeoms.filter(g => {
    const id = Number(g.id);
    const continent = OVERRIDES[id] ?? ISO_TO_CONTINENT[id];
    return continent === continentName;
  });

  if (geoms.length === 0) {
    console.warn(`No geometries found for ${continentName}`);
    return null;
  }

  const merged = topojson.merge(topo, geoms);
  return {
    type: "Feature" as const,
    properties: { name: continentName, color: CONTINENT_COLORS[continentName] },
    geometry: merged,
  };
}).filter(Boolean);

const geojson = {
  type: "FeatureCollection",
  features,
};

const outPath = join(import.meta.dirname, "../src/data/continents.json");
writeFileSync(outPath, JSON.stringify(geojson));
console.log(`Written ${features.length} continent features → ${outPath}`);
