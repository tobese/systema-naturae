const fs = require('fs');

const input = fs.readFileSync('portal/data/color-registry-plantae.txt', 'utf-8');
const lines = input.split('\n');

const themes = [];
const registry = [];

for (const line of lines) {
  const constMatch = line.match(/^const (\w+_THEME): ColorTheme = (.+);$/);
  if (constMatch) {
    const themeName = constMatch[1];
    const themeBody = constMatch[2].trim();
    // Add required animal fields with empty defaults so TypeScript is happy
    const augmented = themeBody.replace(/}$/, ', subfamilyColors: {}, lineageColors: {}, breedGroupColor: "#888", hybridColor: "#888" }');
    themes.push(`const ${themeName}: ColorTheme = ${augmented};`);
  }
  const setMatch = line.match(/^colorRegistry\.set\("([^"]+)", (\w+_THEME)\);$/);
  if (setMatch) {
    registry.push(`  "${setMatch[1]}": ${setMatch[2]},`);
  }
}

const output = `import type { ColorTheme } from "@shared/types";

${themes.join('\n')}

export const COLOR_REGISTRY: Record<string, ColorTheme> = {
${registry.join('\n')}
};
`;

fs.writeFileSync('portal/src/colorRegistryPlantae.ts', output);
console.log(`Wrote ${themes.length} themes and ${registry.length} registry entries to portal/src/colorRegistryPlantae.ts`);
