#!/usr/bin/env node
/**
 * Expand bird family data files to their target species counts.
 * Reads existing files, adds species to reach targets, writes back.
 */
const fs = require('fs');
const path = require('path');

const ROOT = '/Users/tb/Dev/systema-naturae';

function countSpecies(node) {
  let c = 0;
  if (node.rank === 'SPECIES') c++;
  if (node.children) node.children.forEach(x => c += countSpecies(x));
  return c;
}

function findGen(data, name) {
  for (const ch of data.children || []) {
    if (ch.name === name && ch.rank === 'GENUS') return ch;
    const f = findGen(ch, name);
    if (f) return f;
  }
  return null;
}

// Reusable: find or create genus
function ensureGen(data, gname, gdesc, gid, lineage) {
  let g = findGen(data, gname);
  if (!g) {
    g = { id: gid, name: gname, rank: 'GENUS', description: gdesc, lineage, children: [] };
    data.children.push(g);
  }
  return g;
}

function sp(id, name, cn, lineage, cont, ssc, desc) {
  return { id, name, rank: 'SPECIES', commonName: cn, lineage, continents: cont, subspeciesCount: ssc, description: desc };
}

// Load and process a single family
function processFamily(relPath, expandFn) {
  const fp = path.join(ROOT, relPath);
  const data = JSON.parse(fs.readFileSync(fp, 'utf8'));
  const before = countSpecies(data);
  expandFn(data);
  const after = countSpecies(data);
  fs.writeFileSync(fp, JSON.stringify(data, null, 2) + '\n');
  console.log(`  ${path.basename(relPath)}: ${before} → ${after} species`);
}

// ============================================================
// 1. PETROICIDAE (6 → 49)
function expandPetroicidae(d) {
  const p = ensureGen(d, 'Microeca', 'The flycatcher-robins — a genus of small, active robins with a more slender build and flycatching foraging style.', 'GENUS_MICROECA', 'Australasian Robins');
  p.children.push(
    sp('MICROECA_FASCINANS', 'Microeca fascinans', 'Jacky Winter', 'Australasian Robins', ['Australia'], 4, 'A small, pale grey-brown robin with white underparts and a habit of constantly flicking its wings, found across most of Australia in open woodlands.'),
    sp('MICROECA_FLAVIGASTER', 'Microeca flavigaster', 'Lemon-bellied Flycatcher', 'Australasian Robins', ['Australia', 'Asia'], 3, 'A small robin with olive-grey upperparts and a bright yellow belly, found in northern Australia and New Guinea.'),
    sp('MICROECA_GRISEOCEPS', 'Microeca griseoceps', 'Flycatcher-robin', 'Australasian Robins', ['Asia'], 0, 'A tiny olive-grey robin with pale throat and buff underparts, found in lowland forests of New Guinea.'),
    sp('MICROECA_FLAVOVIRESCENS', 'Microeca flavovirescens', 'Olive Flycatcher-robin', 'Australasian Robins', ['Asia'], 0, 'A small olive-green robin with pale yellow underparts, found in lowland forests of the Aru Islands and southern New Guinea.'),
    sp('MICROECA_HEMIXANTHA', 'Microeca hemixantha', 'Golden-bellied Flycatcher-robin', 'Australasian Robins', ['Asia'], 0, 'A small robin with olive upperparts and bright yellow belly, found in the lowland forests of the Moluccas.'),
    sp('MICROECA_PAPUANA', 'Microeca papuana', 'Papuan Flycatcher-robin', 'Australasian Robins', ['Asia'], 0, 'A small olive-brown robin with pale underparts, found in the montane forests of New Guinea.')
  );

  const h = ensureGen(d, 'Heteromyias', 'The ashy robins — medium-sized robins with grey or brown upperparts and white underparts.', 'GENUS_HETEROMYIAS', 'Australasian Robins');
  h.children.push(
    sp('HETEROMYIAS_ALBISPECULARIS', 'Heteromyias albispecularis', 'Ashy Robin', 'Australasian Robins', ['Asia'], 3, 'A medium-sized robin with grey upperparts and white underparts, found in the montane forests of New Guinea.'),
    sp('HETEROMYIAS_CINEREIFRONS', 'Heteromyias cinereifrons', 'White-faced Robin', 'Australasian Robins', ['Australia'], 0, 'A robin with a pale grey face, brown upperparts, and white underparts, found in the rainforests of northeastern Queensland.'),
    sp('HETEROMYIAS_ARMITI', 'Heteromyias armiti', 'Black-cheeked Robin', 'Australasian Robins', ['Asia'], 0, 'A medium-sized robin with black cheeks and white underparts, found in the montane forests of New Guinea.')
  );

  const pe = ensureGen(d, 'Peneothello', 'The slate robins — dark grey robins found in the forests of New Guinea.', 'GENUS_PENEOTHELLO', 'Australasian Robins');
  pe.children.push(
    sp('PENEOTHELLO_CRYPTOLEUCA', 'Peneothello cryptoleuca', 'White-rumped Robin', 'Australasian Robins', ['Asia'], 0, 'A dark grey robin with a contrasting white rump, found in the montane forests of New Guinea.'),
    sp('PENEOTHELLO_CYANUS', 'Peneothello cyanus', 'Slaty Robin', 'Australasian Robins', ['Asia'], 2, 'A uniform slate-grey robin with blackish wings, found in the montane forests of New Guinea.'),
    sp('PENEOTHELLO_BIMACULATA', 'Peneothello bimaculata', 'White-winged Robin', 'Australasian Robins', ['Asia'], 0, 'A dark grey robin with distinctive white wing patches, found in the lowland forests of New Guinea.'),
    sp('PENEOTHELLO_SIGILLATA', 'Peneothello sigillata', 'White-breasted Robin', 'Australasian Robins', ['Asia'], 2, 'A dark slate-grey robin with a pure white breast, found in the montane forests of New Guinea.')
  );

  const po = ensureGen(d, 'Poecilodryas', 'A genus of medium-sized robins with white eyebrows and bold patterns, found in Australia and New Guinea.', 'GENUS_POECILODRYAS', 'Australasian Robins');
  po.children.push(
    sp('POECILODRYAS_CERVINIVENTRIS', 'Poecilodryas cerviniventris', 'Buff-sided Robin', 'Australasian Robins', ['Australia', 'Asia'], 0, 'A robin with dark brown upperparts, bold white eyebrow, and buff underparts, found in lowland forests of northern Australia and New Guinea.'),
    sp('POECILODRYAS_BRACHYURA', 'Poecilodryas brachyura', 'Black-chinned Robin', 'Australasian Robins', ['Asia'], 0, 'A robin with olive-brown upperparts, black chin, and white underparts, found in lowland forests of New Guinea.'),
    sp('POECILODRYAS_HYPOLEUCA', 'Poecilodryas hypoleuca', 'White-winged Robin', 'Australasian Robins', ['Asia'], 0, 'A black-and-white robin with glossy black upperparts and white wing patches, found in lowland forests of New Guinea.'),
    sp('POECILODRYAS_SUPERCILIOSA', 'Poecilodryas superciliosa', 'White-browed Robin', 'Australasian Robins', ['Australia'], 0, 'A robin with dark brown upperparts, bold white eyebrow, and white underparts, found in lowland forests of northeastern Australia.'),
    sp('POECILODRYAS_ALBONOTATA', 'Poecilodryas albonotata', 'Black-throated Robin', 'Australasian Robins', ['Asia'], 0, 'A robin with dark grey upperparts, black throat, and white underparts, found in the montane forests of New Guinea.')
  );

  const m = ensureGen(d, 'Melanodryas', 'A genus of striking black-and-white robins found in Australia.', 'GENUS_MELANODRYAS', 'Australasian Robins');
  m.children.push(
    sp('MELANODRYAS_CUCULLATA', 'Melanodryas cucullata', 'Hooded Robin', 'Australasian Robins', ['Australia'], 3, 'A striking robin with glossy black upperparts, white underparts, and white wing patches, found in dry woodlands across much of Australia.'),
    sp('MELANODRYAS_VITTATA', 'Melanodryas vittata', 'Dusky Robin', 'Australasian Robins', ['Australia'], 0, 'A sombre olive-brown robin with a pale throat and belly, endemic to Tasmania and the Bass Strait islands.')
  );

  const t = ensureGen(d, 'Tregellasia', 'A genus of small, plump robins with pale yellow underparts, found in Australia and New Guinea.', 'GENUS_TREGELLASIA', 'Australasian Robins');
  t.children.push(
    sp('TREGELLASIA_CAPITO', 'Tregellasia capito', 'Pale-yellow Robin', 'Australasian Robins', ['Australia'], 2, 'A small, plump robin with olive-green upperparts and pale yellow underparts, found in the rainforests of eastern Australia.'),
    sp('TREGELLASIA_LEUCOPS', 'Tregellasia leucops', 'White-faced Robin', 'Australasian Robins', ['Asia'], 3, 'A small robin with olive-green upperparts, white face, and yellow underparts, found in the lowland forests of New Guinea.')
  );

  const g = ensureGen(d, 'Gennaeodryas', 'A monotypic genus of olive-yellow robin from New Guinea.', 'GENUS_GENNAEODRYAS', 'Australasian Robins');
  g.children.push(sp('GENNAEODRYAS_PLACENS', 'Gennaeodryas placens', 'Olive-yellow Robin', 'Australasian Robins', ['Asia'], 0, 'A small olive-yellow robin with a pale throat, found in the montane forests of New Guinea.'));

  const eu = ensureGen(d, 'Eugerygone', 'A monotypic genus of small robin with bright red back, from New Guinea.', 'GENUS_EUGERYGONE', 'Australasian Robins');
  eu.children.push(sp('EUGERYGONE_RUBRA', 'Eugerygone rubra', 'Red-backed Robin', 'Australasian Robins', ['Asia'], 0, 'A small robin with the male having a bright crimson back, found in the montane forests of New Guinea.'));

  const pa = ensureGen(d, 'Pachycephalopsis', 'A genus of medium-sized green-backed robins from New Guinea.', 'GENUS_PACHYCEPHALOPSIS', 'Australasian Robins');
  pa.children.push(
    sp('PACHYCEPHALOPSIS_HATTAMENSIS', 'Pachycephalopsis hattamensis', 'Green-backed Robin', 'Australasian Robins', ['Asia'], 0, 'A medium-sized robin with olive-green upperparts and yellow underparts, found in the lowland forests of New Guinea.'),
    sp('PACHYCEPHALOPSIS_POLIOSOMA', 'Pachycephalopsis poliosoma', 'White-eyed Robin', 'Australasian Robins', ['Asia'], 2, 'A medium-sized robin with olive-green upperparts and a distinctive pale eye, found in the montane forests of New Guinea.')
  );

  const mo = ensureGen(d, 'Monachella', 'A monotypic genus of torrent robin from New Guinea.', 'GENUS_MONACHELLA', 'Australasian Robins');
  mo.children.push(sp('MONACHELLA_MUELLERIANA', 'Monachella muelleriana', 'Torrent Robin', 'Australasian Robins', ['Asia'], 2, 'A striking black-and-white robin found along fast-flowing streams in the montane forests of New Guinea.'));

  // Add remaining Petroica species
  const pet = findGen(d, 'Petroica');
  if (pet) pet.children.push(
    sp('PETROICA_AUSTRALIS', 'Petroica australis', 'New Zealand Robin', 'Australasian Robins', ['Australia'], 2, 'A large robin endemic to New Zealand, with dark grey upperparts and pale underparts, known for its confiding nature.'),
    sp('PETROICA_TRAVERSI', 'Petroica traversi', 'Chatham Robin', 'Australasian Robins', ['Australia'], 0, 'A small endangered robin endemic to the Chatham Islands of New Zealand, saved from extinction by translocations.'),
    sp('PETROICA_MACROCEPHALA', 'Petroica macrocephala', 'Tomtit', 'Australasian Robins', ['Australia'], 5, 'A small active robin of New Zealand forests, with the male having a black head, white cap, and yellow breast.'),
    sp('PETROICA_GOODENOVII', 'Petroica goodenovii', 'Red-capped Robin', 'Australasian Robins', ['Australia'], 0, 'A striking robin with glossy black upperparts, brilliant red cap, and white underparts, found in dry woodlands of inland Australia.'),
    sp('PETROICA_MULTICOLOR', 'Petroica multicolor', 'Pacific Robin', 'Australasian Robins', ['Australia'], 4, 'A robin found on Norfolk Island and the southwest Pacific, with glossy black upperparts and scarlet breast.'),
    sp('PETROICA_PUSILLA', 'Petroica pusilla', 'Banded Yellow Robin', 'Australasian Robins', ['Australia', 'Asia'], 3, 'A small active robin with olive-brown upperparts and yellow underparts, found in eastern Australia and New Guinea.'),
    sp('PETROICA_VITTATA', 'Petroica vittata', 'Dusky Robin', 'Australasian Robins', ['Australia'], 0, 'A sombre olive-brown robin with a pale throat, found in Tasmania and the Bass Strait islands.')
  );

  const eops = findGen(d, 'Eopsaltria');
  if (eops) eops.children.push(
    sp('EOPSALTRIA_FLAVIVENTRIS', 'Eopsaltria flaviventris', 'Yellow-bellied Robin', 'Australasian Robins', ['Australia', 'Asia'], 2, 'A plump robin with bright yellow underparts and olive-grey upperparts, found in northern Australia and southern New Guinea.'),
    sp('EOPSALTRIA_PULVERULENTA', 'Eopsaltria pulverulenta', 'Mangrove Robin', 'Australasian Robins', ['Australia', 'Asia'], 2, 'A pale grey robin with white underparts, restricted to mangroves of northern Australia and New Guinea.')
  );

  const dry = findGen(d, 'Drymodes');
  if (dry) dry.children.push(
    sp('DRYMODES_SUPERCILIARIS', 'Drymodes superciliaris', 'Northern Scrub Robin', 'Australasian Robins', ['Asia'], 0, 'A long-legged, ground-dwelling robin with brown upperparts and bold white eyebrow, found in New Guinea.')
  );
}

// 2. COTINGIDAE (17 → 66)
function expandCotingidae(d) {
  const proc = findGen(d, 'Procnias');
  if (proc) proc.children.push(
    sp('PROCNIAS_ALBUS', 'Procnias albus', 'White Bellbird', 'Cotingas', ['South America'], 0, 'An entirely white bellbird with a black fleshy wattle, found in the Guiana Shield and northern Amazon. Its call is among the loudest of any bird.'),
    sp('PROCNIAS_AVERANO', 'Procnias averano', 'Bearded Bellbird', 'Cotingas', ['South America'], 0, 'A bellbird with brown upperparts, white underparts, and a distinctive beard-like wattle, found in northern South America.'),
    sp('PROCNIAS_TRICARUNCULATUS', 'Procnias tricarunculatus', 'Three-wattled Bellbird', 'Cotingas', ['North America'], 0, 'A chestnut-brown bellbird with a white head and three long black wattles, found in the cloud forests of Costa Rica and Panama.')
  );

  const lip = findGen(d, 'Lipaugus');
  if (lip) lip.children.push(
    sp('LIPAUGUS_UNIRUFUS', 'Lipaugus unirufus', 'Rufous Piha', 'Cotingas', ['North America', 'South America'], 0, 'A rich rufous piha found in lowland rainforests of Central America from Mexico to Panama.'),
    sp('LIPAUGUS_UROPYGIALIS', 'Lipaugus uropygialis', 'Scimitar-winged Piha', 'Cotingas', ['South America'], 0, 'A grey piha with rufous rump and modified wing feathers, found in the cloud forests of the Andes.'),
    sp('LIPAUGUS_CONDITUS', 'Lipaugus conditus', 'Grey-winged Cotinga', 'Cotingas', ['South America'], 0, 'A plain grey cotinga restricted to the Atlantic Forest of southeastern Brazil, considered vulnerable.'),
    sp('LIPAUGUS_WEBERI', 'Lipaugus weberi', 'Chestnut-capped Piha', 'Cotingas', ['South America'], 0, 'A grey piha with a chestnut cap, found in the Colombian Andes. Critically endangered.'),
    sp('LIPAUGUS_ATER', 'Lipaugus ater', 'Black-and-gold Cotinga', 'Cotingas', ['South America'], 0, 'A striking cotinga with glossy black upperparts and golden-yellow underparts, from the Atlantic Forest of Brazil.')
  );

  const cot = findGen(d, 'Cotinga');
  if (cot) cot.children.push(
    sp('COTINGA_NATTERERII', 'Cotinga nattererii', 'Blue Cotinga', 'Cotingas', ['North America', 'South America'], 0, 'A brilliant turquoise-blue cotinga with violet throat, found from Panama to northwestern South America.')
  );

  // Add Xipholena
  d.children.push({
    id: 'GENUS_XIPHOLENA', name: 'Xipholena', rank: 'GENUS', commonName: 'White-winged Cotingas',
    description: 'A genus of spectacular cotingas with the males in brilliant purple or wine-red plumage and contrasting white wings.',
    lineage: 'Cotingas', continents: ['South America'], subspeciesCount: 0,
    children: [
      sp('XIPHOLENA_PUNICEA', 'Xipholena punicea', 'Pompadour Cotinga', 'Cotingas', ['South America'], 0, 'A stunning cotinga with the male brilliant wine-red with white wings, found across the Amazon basin.'),
      sp('XIPHOLENA_ATROPURPUREA', 'Xipholena atropurpurea', 'White-winged Cotinga', 'Cotingas', ['South America'], 0, 'A cotinga with deep purple-red body and white wings, endemic to the Atlantic Forest of Brazil. Endangered.'),
      sp('XIPHOLENA_LAMELLIPENNIS', 'Xipholena lamellipennis', 'White-tailed Cotinga', 'Cotingas', ['South America'], 0, 'A spectacular cotinga with glossy purple body and white tail, found in the Guiana Shield.')
    ]
  });

  d.children.push({
    id: 'GENUS_PHOENICIRCUS', name: 'Phoenicircus', rank: 'GENUS', commonName: 'Red Cotingas',
    description: 'A genus of spectacular brilliant-red cotingas found in the Amazon basin and Guiana Shield.',
    lineage: 'Cotingas', continents: ['South America'], subspeciesCount: 0,
    children: [
      sp('PHOENICIRCUS_CARNIFEX', 'Phoenicircus carnifex', 'Guianan Red Cotinga', 'Cotingas', ['South America'], 0, 'A brilliant crimson cotinga with black-edged wings, found in the Guiana Shield.'),
      sp('PHOENICIRCUS_NIGRICOLLIS', 'Phoenicircus nigricollis', 'Black-necked Red Cotinga', 'Cotingas', ['South America'], 0, 'A brilliant crimson cotinga with a black throat, found in the western Amazon basin.')
    ]
  });

  d.children.push({
    id: 'GENUS_IODOPLEURA', name: 'Iodopleura', rank: 'GENUS', commonName: 'Purpletufts',
    description: 'Tiny cotingas with distinctive purple tufts of feathers on the flanks, found in the Amazon basin.',
    lineage: 'Cotingas', continents: ['South America'], subspeciesCount: 0,
    children: [
      sp('IODOPLEURA_PIPRA', 'Iodopleura pipra', 'Buff-throated Purpletuft', 'Cotingas', ['South America'], 0, 'A tiny cotinga with violet upperparts and purple flank tufts, found in the Amazon basin.'),
      sp('IODOPLEURA_LEUCOPYGIA', 'Iodopleura leucopygia', 'White-rumped Purpletuft', 'Cotingas', ['South America'], 0, 'A tiny cotinga with violet upperparts and white rump, found in the Guiana Shield.'),
      sp('IODOPLEURA_ISABELLAE', 'Iodopleura isabellae', 'White-browed Purpletuft', 'Cotingas', ['South America'], 0, 'A tiny cotinga with brown upperparts and white eyebrow, found in the western Amazon.')
    ]
  });

  d.children.push({
    id: 'GENUS_TIJUCA', name: 'Tijuca', rank: 'GENUS', commonName: 'Berryeaters',
    description: 'A genus of cotingas endemic to the Atlantic Forest of Brazil, with striking black-and-gold or grey plumage.',
    lineage: 'Cotingas', continents: ['South America'], subspeciesCount: 0,
    children: [
      sp('TIJUCA_ATRA', 'Tijuca atra', 'Black-and-gold Cotinga', 'Cotingas', ['South America'], 0, 'A striking cotinga with glossy black upperparts and golden-yellow belly, endemic to the Atlantic Forest.'),
      sp('TIJUCA_CONDITA', 'Tijuca condita', 'Grey-winged Cotinga', 'Cotingas', ['South America'], 0, 'A plain grey cotinga restricted to the Atlantic Forest of Brazil, discovered in 1982.')
    ]
  });

  d.children.push({
    id: 'GENUS_CARPORNIS', name: 'Carpornis', rank: 'GENUS', commonName: 'Berryeaters',
    description: 'A genus of medium-sized cotingas with hooded heads, endemic to the Atlantic Forest of Brazil.',
    lineage: 'Cotingas', continents: ['South America'], subspeciesCount: 0,
    children: [
      sp('CARPORNIS_CUCULLATA', 'Carpornis cucullata', 'Hooded Berryeater', 'Cotingas', ['South America'], 0, 'A cotinga with olive-green upperparts, black hood, and yellow underparts, endemic to the Atlantic Forest.'),
      sp('CARPORNIS_MELANOCEPHALA', 'Carpornis melanocephala', 'Black-headed Berryeater', 'Cotingas', ['South America'], 0, 'A cotinga with olive-green upperparts, black head, and bright yellow underparts, endemic to the Atlantic Forest.')
    ]
  });

  d.children.push({
    id: 'GENUS_SNOWORNIS', name: 'Snowornis', rank: 'GENUS', commonName: 'Pihas',
    description: 'A genus of dull-plumaged pihas found in the cloud forests of the Andes.',
    lineage: 'Cotingas', continents: ['South America'], subspeciesCount: 0,
    children: [
      sp('SNOWORNIS_CRYPTOLOPHUS', 'Snowornis cryptolophus', 'Olivaceous Piha', 'Cotingas', ['South America'], 0, 'A dull olive-green piha with a pale belly, found in the cloud forests of the Andes.'),
      sp('SNOWORNIS_SUBALARIS', 'Snowornis subalaris', 'Grey-tailed Piha', 'Cotingas', ['South America'], 0, 'An olive-green piha with a distinctive grey tail, found in the cloud forests of the Andes.')
    ]
  });

  d.children.push({
    id: 'GENUS_PORPHYROLAEMA', name: 'Porphyrolaema', rank: 'GENUS', commonName: 'Purple-throated Cotinga',
    description: 'A monotypic genus of stunning cotinga with a brilliant purple throat.',
    lineage: 'Cotingas', continents: ['South America'], subspeciesCount: 0,
    children: [
      sp('PORPHYROLAEMA_PORPHYROLAEMA', 'Porphyrolaema porphyrolaema', 'Purple-throated Cotinga', 'Cotingas', ['South America'], 0, 'A stunning cotinga with brilliant purple throat, white underparts, and black upperparts with blue shoulders, from the western Amazon.')
    ]
  });

  d.children.push({
    id: 'GENUS_PYRODERUS', name: 'Pyroderus', rank: 'GENUS', commonName: 'Red-ruffed Fruitcrow',
    description: 'A monotypic genus of massive black fruitcrow with a brilliant red throat patch.',
    lineage: 'Cotingas', continents: ['South America'], subspeciesCount: 0,
    children: [
      sp('PYRODERUS_SCUTATUS', 'Pyroderus scutatus', 'Red-ruffed Fruitcrow', 'Cotingas', ['South America'], 4, 'A massive black cotinga with a brilliant red-orange throat patch, found from Colombia to Argentina.')
    ]
  });

  d.children.push({
    id: 'GENUS_HAEMATODERUS', name: 'Haematoderus', rank: 'GENUS', commonName: 'Crimson Fruitcrow',
    description: 'A monotypic genus of spectacular all-red fruitcrow.',
    lineage: 'Cotingas', continents: ['South America'], subspeciesCount: 0,
    children: [
      sp('HAEMATODERUS_MILITARIS', 'Haematoderus militaris', 'Crimson Fruitcrow', 'Cotingas', ['South America'], 0, 'A spectacular cotinga with the male entirely crimson-red, found in the Guiana Shield and northern Brazil.')
    ]
  });

  d.children.push({
    id: 'GENUS_GYMNODERUS', name: 'Gymnoderus', rank: 'GENUS', commonName: 'Bare-necked Fruitcrow',
    description: 'A monotypic genus of black fruitcrow with bare blue facial skin.',
    lineage: 'Cotingas', continents: ['South America'], subspeciesCount: 0,
    children: [
      sp('GYMNODERUS_FOETIDUS', 'Gymnoderus foetidus', 'Bare-necked Fruitcrow', 'Cotingas', ['South America'], 0, 'A large cotinga with the male entirely black with bare blue facial skin, found in the Amazon basin.')
    ]
  });

  d.children.push({
    id: 'GENUS_PERISSOCEPHALUS', name: 'Perissocephalus', rank: 'GENUS', commonName: 'Capuchinbird',
    description: 'A monotypic genus of bizarre cotinga with a distinctive mooing call.',
    lineage: 'Cotingas', continents: ['South America'], subspeciesCount: 0,
    children: [
      sp('PERISSOCEPHALUS_TRICOLOR', 'Perissocephalus tricolor', 'Capuchinbird', 'Cotingas', ['South America'], 0, 'A bizarre cotinga with bare blue-grey face, black cap, and rich brown body. Its far-carrying mooing call is distinctive in the Guiana Shield.')
    ]
  });

  const ceph = findGen(d, 'Cephalopterus');
  if (ceph) ceph.children.push(
    sp('CEPHALOPTERUS_GLABRICOLLIS', 'Cephalopterus glabricollis', 'Bare-necked Umbrellabird', 'Cotingas', ['North America'], 0, 'A large black cotinga with retractable crest and bare red throat patch, found in Costa Rica and Panama.'),
    sp('CEPHALOPTERUS_PENDULIGER', 'Cephalopterus penduliger', 'Long-wattled Umbrellabird', 'Cotingas', ['South America'], 0, 'A large black cotinga with umbrella crest and long pendulous wattle, found in Colombia and Ecuador.')
  );

  d.children.push({
    id: 'GENUS_PIPREOLA', name: 'Pipreola', rank: 'GENUS', commonName: 'Fruiteaters',
    description: 'A genus of colourful, fruit-eating cotingas found in the cloud forests of the Andes. Males are brilliantly patterned with green, red, yellow, and black.',
    lineage: 'Cotingas', continents: ['South America'], subspeciesCount: 0,
    children: [
      sp('PIPREOLA_CHLOROLEPIDOTA', 'Pipreola chlorolepidota', 'Fiery-throated Fruiteater', 'Cotingas', ['South America'], 0, 'A fruiteater with green upperparts and brilliant orange throat, found in Colombia and Ecuador.'),
      sp('PIPREOLA_FRONTALIS', 'Pipreola frontalis', 'Scarlet-breasted Fruiteater', 'Cotingas', ['South America'], 2, 'A fruiteater with green upperparts and scarlet breast band, found from Colombia to Bolivia.'),
      sp('PIPREOLA_LUBOMIRSKII', 'Pipreola lubomirskii', 'Black-chested Fruiteater', 'Cotingas', ['South America'], 0, 'A fruiteater with green upperparts and black breast band, found from Colombia to Peru.'),
      sp('PIPREOLA_PULCHRA', 'Pipreola pulchra', 'Masked Fruiteater', 'Cotingas', ['South America'], 0, 'A fruiteater with green upperparts and black face mask, endemic to the montane forests of Peru.'),
      sp('PIPREOLA_AUREOPECTUS', 'Pipreola aureopectus', 'Golden-breasted Fruiteater', 'Cotingas', ['South America'], 2, 'A stunning fruiteater with green upperparts and golden-yellow breast, found from Colombia to Bolivia.'),
      sp('PIPREOLA_JUCUNDA', 'Pipreola jucunda', 'Orange-breasted Fruiteater', 'Cotingas', ['South America'], 0, 'A fruiteater with green upperparts and bright orange breast, found in Colombia and Ecuador.'),
      sp('PIPREOLA_ARCSUATA', 'Pipreola arcuata', 'Barred Fruiteater', 'Cotingas', ['South America'], 0, 'A striking fruiteater with green upperparts and barred black-and-yellow underparts, found from Colombia to Bolivia.'),
      sp('PIPREOLA_INTERMEDIA', 'Pipreola intermedia', 'Chestnut-naped Fruiteater', 'Cotingas', ['South America'], 2, 'A fruiteater with green upperparts and chestnut nape, found from Peru to Bolivia.'),
      sp('PIPREOLA_RIEFFERII', 'Pipreola riefferii', 'Green-and-black Fruiteater', 'Cotingas', ['South America'], 5, 'A fruiteater with green upperparts and barred black-and-yellow underparts, found from Colombia to Peru.')
    ]
  });

  d.children.push({
    id: 'GENUS_AMPELIOIDES', name: 'Ampelioides', rank: 'GENUS', commonName: 'Scaled Fruiteater',
    description: 'A monotypic genus of fruiteater with distinctive scaled underparts.',
    lineage: 'Cotingas', continents: ['South America'], subspeciesCount: 0,
    children: [
      sp('AMPELIOIDES_TSCHUDII', 'Ampelioides tschudii', 'Scaled Fruiteater', 'Cotingas', ['South America'], 0, 'A distinctive fruiteater with green upperparts and bold black scaling on the yellow underparts, found in the Andes.')
    ]
  });

  d.children.push({
    id: 'GENUS_PHYTOTOMA', name: 'Phytotoma', rank: 'GENUS', commonName: 'Plantcutters',
    description: 'A genus of cotingas with short stout bills adapted for feeding on leaves and buds, found in southern South America.',
    lineage: 'Cotingas', continents: ['South America'], subspeciesCount: 0,
    children: [
      sp('PHYTOTOMA_RAIMONDII', 'Phytotoma raimondii', 'Peruvian Plantcutter', 'Cotingas', ['South America'], 0, 'A cotinga with grey upperparts and short stout bill, endemic to the dry forests of northwestern Peru. Endangered.'),
      sp('PHYTOTOMA_RUTILA', 'Phytotoma rutila', 'White-tipped Plantcutter', 'Cotingas', ['South America'], 3, 'A cotinga with white wing patches, found from Bolivia to Argentina.'),
      sp('PHYTOTOMA_RARA', 'Phytotoma rara', 'Rufous-tailed Plantcutter', 'Cotingas', ['South America'], 0, 'A cotinga with brown upperparts and rufous tail, found in Chile and Argentina.')
    ]
  });

  d.children.push({
    id: 'GENUS_ZARATORNIS', name: 'Zaratornis', rank: 'GENUS', commonName: 'White-cheeked Cotinga',
    description: 'A monotypic genus restricted to high-altitude Polylepis forests of the Peruvian Andes.',
    lineage: 'Cotingas', continents: ['South America'], subspeciesCount: 0,
    children: [
      sp('ZARATORNIS_STRESEMANNI', 'Zaratornis stresemanni', 'White-cheeked Cotinga', 'Cotingas', ['South America'], 0, 'A grey-brown cotinga with white cheeks, found in high-altitude Polylepis forests of Peru.')
    ]
  });

  d.children.push({
    id: 'GENUS_CONIOPTILON', name: 'Conioptilon', rank: 'GENUS', commonName: 'Black-faced Cotinga',
    description: 'A monotypic genus of cotinga with a distinctive black face, found in the western Amazon.',
    lineage: 'Cotingas', continents: ['South America'], subspeciesCount: 0,
    children: [
      sp('CONIOPTILON_MCILHENNYI', 'Conioptilon mcilhennyi', 'Black-faced Cotinga', 'Cotingas', ['South America'], 0, 'A distinctive cotinga with a black face and throat, grey body, and black wings, found in the western Amazon.')
    ]
  });
}

// 3. ACANTHIZIDAE (18 → 67)
function expandAcanthizidae(d) {
  const a = findGen(d, 'Acanthiza');
  if (a) a.children.push(
    sp('ACANTHIZA_REGULOIDES', 'Acanthiza reguloides', 'Buff-rumped Thornbill', 'Australasian Warblers', ['Australia'], 4, 'A small thornbill with a buff rump, found in forests of eastern Australia.'),
    sp('ACANTHIZA_EWINGII', 'Acanthiza ewingii', 'Tasmanian Thornbill', 'Australasian Warblers', ['Australia'], 0, 'A small olive-brown thornbill, endemic to Tasmania.'),
    sp('ACANTHIZA_HERRINGI', 'Acanthiza herringi', 'White-browed Thornbill', 'Australasian Warblers', ['Australia'], 0, 'A small thornbill with bold white eyebrow, found in dry woodlands of southeastern Australia.'),
    sp('ACANTHIZA_IREDALEI', 'Acanthiza iredalei', 'Slaty-backed Thornbill', 'Australasian Warblers', ['Australia'], 2, 'A small thornbill of arid and semi-arid woodlands of inland Australia.'),
    sp('ACANTHIZA_ROBUSTIROSTRIS', 'Acanthiza robustirostris', 'Slender-billed Thornbill', 'Australasian Warblers', ['Australia'], 0, 'A small thornbill of arid shrublands of central Australia.'),
    sp('ACANTHIZA_INORNATA', 'Acanthiza inornata', 'Western Thornbill', 'Australasian Warblers', ['Australia'], 0, 'A small thornbill endemic to southwestern Australia.'),
    sp('ACANTHIZA_UROPYGIALIS', 'Acanthiza uropygialis', 'Chestnut-rumped Thornbill', 'Australasian Warblers', ['Australia'], 0, 'A small thornbill with chestnut rump, found in dry woodlands of inland Australia.')
  );

  const ser = findGen(d, 'Sericornis');
  if (ser) ser.children.push(
    sp('SERICORNIS_CITREOGULARIS', 'Sericornis citreogularis', 'Yellow-throated Scrubwren', 'Australasian Warblers', ['Australia'], 0, 'A scrubwren with olive-green upperparts and bright yellow throat, found in rainforests of northeastern Australia.'),
    sp('SERICORNIS_MAGNIROSTRIS', 'Sericornis magnirostris', 'Large-billed Scrubwren', 'Australasian Warblers', ['Australia', 'Asia'], 3, 'A scrubwren with a stout bill, found in New Guinea and northeastern Australia.'),
    sp('SERICORNIS_BECCARI', 'Sericornis beccarii', 'Beccari\'s Scrubwren', 'Australasian Warblers', ['Asia'], 4, 'A small scrubwren found in lowland forests of New Guinea and the Moluccas.'),
    sp('SERICORNIS_NOVAEGUINEAE', 'Sericornis novaeguineae', 'Large Scrubwren', 'Australasian Warblers', ['Asia'], 0, 'A large scrubwren found in the montane forests of New Guinea.'),
    sp('SERICORNIS_SPILODERA', 'Sericornis spilodera', 'Pale-billed Scrubwren', 'Australasian Warblers', ['Asia'], 0, 'A scrubwren with a pale horn-coloured bill, found in the montane forests of New Guinea.')
  );

  const g = findGen(d, 'Gerygone');
  if (g) g.children.push(
    sp('GERYGONE_OLIVACEA', 'Gerygone olivacea', 'White-throated Gerygone', 'Australasian Warblers', ['Australia', 'Asia'], 2, 'A small warbler with olive upperparts and white underparts, found in northern and eastern Australia.'),
    sp('GERYGONE_TENEBROSA', 'Gerygone tenebrosa', 'Dusky Gerygone', 'Australasian Warblers', ['Australia'], 0, 'A small dark warbler found in mangroves of northwestern Australia.'),
    sp('GERYGONE_ALBOGULARIS', 'Gerygone albogularis', 'White-throated Gerygone', 'Australasian Warblers', ['Asia', 'Australia'], 0, 'A small warbler found in New Guinea and the Solomon Islands.'),
    sp('GERYGONE_CHRYSOCRAS', 'Gerygone chrysocras', 'Yellow-bellied Gerygone', 'Australasian Warblers', ['Asia'], 0, 'A small warbler with bright yellow underparts, found in New Guinea.')
  );

  const c = findGen(d, 'Cincloramphus');
  if (c) c.children.push(
    sp('CINCLORAMPHUS_MACRURUS', 'Cincloramphus macrurus', 'Papuan Grassbird', 'Australasian Warblers', ['Asia'], 2, 'A large grassbird with heavily streaked brown upperparts, found in grasslands of New Guinea.')
  );

  // Add new genera
  const newGenera = [
    {
      id: 'GENUS_CALAMANTHUS', name: 'Calamanthus', commonName: 'Fieldwrens',
      desc: 'Small, ground-dwelling warblers with finely streaked plumage, endemic to Australia.',
      species: [
        sp('CALAMANTHUS_FULIGINOSUS', 'Calamanthus fuliginosus', 'Striated Fieldwren', 'Australasian Warblers', ['Australia'], 3, 'A small heavily streaked warbler of coastal heathlands in southeastern Australia.'),
        sp('CALAMANTHUS_CAMPESTRIS', 'Calamanthus campestris', 'Rufous Fieldwren', 'Australasian Warblers', ['Australia'], 4, 'A small streaked warbler of arid scrublands across southern Australia.')
      ]
    },
    {
      id: 'GENUS_HYLACOLA', name: 'Hylacola', commonName: 'Heathwrens',
      desc: 'Small secretive warblers with rufous rumps, endemic to southern Australia.',
      species: [
        sp('HYLACOLA_CAUTA', 'Hylacola cauta', 'Shy Heathwren', 'Australasian Warblers', ['Australia'], 3, 'A small secretive warbler of mallee and heathlands in southern Australia.'),
        sp('HYLACOLA_PYRENOPYGIA', 'Hylacola pyrrhopygia', 'Chestnut-rumped Heathwren', 'Australasian Warblers', ['Australia'], 0, 'A small warbler with chestnut rump, found in heathlands of southeastern Australia.')
      ]
    },
    {
      id: 'GENUS_OREOSCOPUS', name: 'Oreoscopus', commonName: 'Fernwren',
      desc: 'A monotypic genus of fernwren from Queensland rainforests.',
      species: [
        sp('OREOSCOPUS_GUTTURALIS', 'Oreoscopus gutturalis', 'Fernwren', 'Australasian Warblers', ['Australia'], 0, 'A small dark warbler with white throat, found in dense understorey of mountain rainforests in northeastern Queensland.')
      ]
    },
    {
      id: 'GENUS_ORIGMA', name: 'Origma', commonName: 'Rock-warblers',
      desc: 'Small active warblers of rocky habitats in Australia and New Guinea.',
      species: [
        sp('ORIGMA_SOLITARIA', 'Origma solitaria', 'Rockwarbler', 'Australasian Warblers', ['Australia'], 0, 'A small dark grey warbler with rufous rump, endemic to sandstone gorges of the Sydney region.'),
        sp('ORIGMA_RUFOGULARIS', 'Origma rufogularis', 'Rufous-throated Rockwarbler', 'Australasian Warblers', ['Asia'], 0, 'A small warbler with rufous throat, found in rocky hills of southern New Guinea.')
      ]
    },
    {
      id: 'GENUS_ACANTHORNIS', name: 'Acanthornis', commonName: 'Scrubtit',
      desc: 'A monotypic genus of scrubtit from Tasmanian rainforests.',
      species: [
        sp('ACANTHORNIS_MAGNA', 'Acanthornis magna', 'Scrubtit', 'Australasian Warblers', ['Australia'], 0, 'A small olive-brown bird with white throat, found in the dense understorey of Tasmanian temperate rainforests.')
      ]
    },
    {
      id: 'GENUS_APHELOCEPHALA', name: 'Aphelocephala', commonName: 'Whitefaces',
      desc: 'Small grey-brown warblers with distinctive white faces, endemic to Australia.',
      species: [
        sp('APHELOCEPHALA_LEUCOPSIS', 'Aphelocephala leucopsis', 'Southern Whiteface', 'Australasian Warblers', ['Australia'], 4, 'A small warbler with white face, found in dry woodlands across southern Australia.'),
        sp('APHELOCEPHALA_PECTORALIS', 'Aphelocephala pectoralis', 'Chestnut-breasted Whiteface', 'Australasian Warblers', ['Australia'], 0, 'A small warbler with chestnut breast band, found in arid shrublands of central Australia.'),
        sp('APHELOCEPHALA_NIGRICINCTA', 'Aphelocephala nigricincta', 'Banded Whiteface', 'Australasian Warblers', ['Australia'], 0, 'A small warbler with black breast band, found in stony arid scrublands of inland Australia.')
      ]
    },
    {
      id: 'GENUS_PYRRHOLAEMUS', name: 'Pyrrholaemus', commonName: 'Redthroat',
      desc: 'Small ground-dwelling warblers with red-brown throats, endemic to Australia.',
      species: [
        sp('PYRRHOLAEMUS_BRUNNEUS', 'Pyrrholaemus brunneus', 'Redthroat', 'Australasian Warblers', ['Australia'], 0, 'A small warbler with red-brown throat patch, found in arid scrublands across Australia.'),
        sp('PYRRHOLAEMUS_SAGITTATUS', 'Pyrrholaemus sagittatus', 'Speckled Warbler', 'Australasian Warblers', ['Australia'], 0, 'A small warbler with heavily streaked upperparts, found in rocky woodlands of eastern Australia.')
      ]
    },
    {
      id: 'GENUS_PACHYCARE', name: 'Pachycare', commonName: 'Goldenface',
      desc: 'A monotypic genus of goldenface from the montane forests of New Guinea.',
      species: [
        sp('PACHYCARE_FLAVOGRISEA', 'Pachycare flavogrisea', 'Goldenface', 'Australasian Warblers', ['Asia'], 3, 'A small active warbler with bright yellow face, found in the montane forests of New Guinea.')
      ]
    }
  ];
  for (const ng of newGenera) {
    d.children.push({
      id: ng.id, name: ng.name, rank: 'GENUS', commonName: ng.commonName,
      description: ng.desc, lineage: 'Australasian Warblers', children: ng.species
    });
  }
}

// 10. PARADISAEIDAE (9 → 45)
function expandParadisaeidae(d) {
  // Add more genera/species
  const parad = findGen(d, 'Paradisaea');
  if (parad) parad.children.push(
    sp('PARADISAEA_MINOR', 'Paradisaea minor', 'Lesser Bird of Paradise', 'Paradisaea', ['Oceania'], 0, 'A smaller relative of the greater bird of paradise, found in lowland forests of New Guinea. Males have elongated yellow flank plumes.'),
    sp('PARADISAEA_GUILLELMI', 'Paradisaea guilielmi', 'Emperor Bird of Paradise', 'Paradisaea', ['Oceania'], 0, 'A striking species with brilliant yellow flank plumes and an emerald-green throat, found in hill forests of New Guinea.'),
    sp('PARADISAEA_DECORA', 'Paradisaea decora', 'Goldie\'s Bird of Paradise', 'Paradisaea', ['Oceania'], 0, 'A spectacular bird of paradise with crimson flank plumes, found only on Fergusson and Normanby islands in the D\'Entrecasteaux Archipelago.')
  );

  const loph = findGen(d, 'Lophorina');
  if (loph) loph.children.push(
    sp('LOPHORINA_INTERCEDENS', 'Lophorina intercedens', 'Crescent-caped Lophorina', 'Lophorina', ['Oceania'], 0, 'A recently recognized species from eastern New Guinea, with a distinctive iridescent cape used in courtship.'),
    sp('LOPHORINA_SUPERBA', 'Lophorina superba', 'Superb Bird of Paradise', 'Lophorina', ['Oceania'], 3, 'Famous for its remarkable courtship display in which the male erects a highly iridescent blue breast shield and cape to form a black oval with two bright blue crescents.')
  );

  // Add Parotia
  d.children.push({
    id: 'GENUS_PAROTIA', name: 'Parotia', rank: 'GENUS', commonName: 'Six-wired Birds of Paradise',
    description: 'Medium-sized birds of paradise with six wire-like head plumes and elaborate ballerina-like courtship dances on forest-floor display arenas.',
    lineage: 'Parotia',
    children: [
      sp('PAROTIA_SEFILATA', 'Parotia sefilata', 'Western Parotia', 'Parotia', ['Oceania'], 0, 'A stunning bird of paradise with six wire-like head plumes and a brilliant iridescent breast shield. Males perform an intricate ballerina dance on a cleared forest floor arena.'),
      sp('PAROTIA_CAROLAE', 'Parotia carolae', 'Queen Carola\'s Parotia', 'Parotia', ['Oceania'], 2, 'Named after Queen Carola of Saxony, this species has striking coppery-bronze upperparts and six wire-like head plumes.'),
      sp('PAROTIA_BERLEPSCHI', 'Parotia berlepschi', 'Bronze Parotia', 'Parotia', ['Oceania'], 0, 'A little-known parotia endemic to the Foja Mountains of New Guinea, with bronze-tinted plumage.'),
      sp('PAROTIA_LAWESII', 'Parotia lawesii', 'Lawes\'s Parotia', 'Parotia', ['Oceania'], 0, 'A parotia found in southeastern New Guinea, with six wire-like head plumes and a spectacular courtship dance.'),
      sp('PAROTIA_HELENAE', 'Parotia helenae', 'Eastern Parotia', 'Parotia', ['Oceania'], 0, 'A parotia restricted to the mountains of southeastern Papua New Guinea, named after Princess Helena of the United Kingdom.')
    ]
  });

  // Add Ptiloris (riflebirds)
  d.children.push({
    id: 'GENUS_PTILORIS', name: 'Ptiloris', rank: 'GENUS', commonName: 'Riflebirds',
    description: 'Medium-sized birds of paradise with curved bills and highly iridescent plumage, named for their rifle-like calls. They are the most aggressive of the birds of paradise, defending feeding territories.',
    lineage: 'Ptiloris',
    children: [
      sp('PTILORIS_MAGNIFICUS', 'Ptiloris magnificus', 'Magnificent Riflebird', 'Ptiloris', ['Oceania', 'Asia'], 0, 'A striking riflebird with iridescent blue-green plumage and a long curved bill, found in New Guinea and Cape York. Males display on exposed perches, raising their wings into a wide V-shape.'),
      sp('PTILORIS_INTERCEDENS', 'Ptiloris intercedens', 'Eastern Riflebird', 'Ptiloris', ['Oceania'], 0, 'A riflebird endemic to eastern New Guinea, with brilliant metallic green-blue plumage.'),
      sp('PTILORIS_PARADISEUS', 'Ptiloris paradiseus', 'Paradise Riflebird', 'Ptiloris', ['Australia'], 0, 'An Australian riflebird with exquisite iridescent plumage, found in the rainforests of eastern Australia.'),
      sp('PTILORIS_VICTORIAE', 'Ptiloris victoriae', 'Victoria\'s Riflebird', 'Ptiloris', ['Australia'], 0, 'Named after Queen Victoria, this riflebird is found in the rainforests of northeastern Queensland.')
    ]
  });

  // Add Epimachus (sicklebills)
  d.children.push({
    id: 'GENUS_EPIMACHUS', name: 'Epimachus', rank: 'GENUS', commonName: 'Sicklebills',
    description: 'Large birds of paradise with extremely long, decurved sickle-shaped bills and spectacular elongated tail feathers.',
    lineage: 'Epimachus',
    children: [
      sp('EPIMACHUS_FASTUOSUS', 'Epimachus fastuosus', 'Black Sicklebill', 'Epimachus', ['Oceania'], 0, 'A large, spectacular bird of paradise with a long sickle-shaped bill and an enormous fan-shaped tail, found in the montane forests of New Guinea.'),
      sp('EPIMACHUS_ALBERTISI', 'Epimachus albertisi', 'Brown Sicklebill', 'Epimachus', ['Oceania'], 0, 'A sicklebill with rich brown plumage and an extremely long decurved bill, found in the highlands of New Guinea.'),
      sp('EPIMACHUS_MEYERI', 'Epimachus meyeri', 'Long-tailed Paradigalla', 'Epimachus', ['Oceania'], 0, 'A sicklebill with striking blue facial wattles and an extremely long graduated tail.')
    ]
  });

  // Add Astrapia
  d.children.push({
    id: 'GENUS_ASTRAPIA', name: 'Astrapia', rank: 'GENUS', commonName: 'Astrapias',
    description: 'Long-tailed birds of paradise with iridescent plumage in metallic greens, blues, and purples.',
    lineage: 'Astrapia',
    children: [
      sp('ASTRAPIA_NIGRA', 'Astrapia nigra', 'Arfak Astrapia', 'Astrapia', ['Oceania'], 0, 'A stunning astrapia with iridescent green and blue plumage, found in the Arfak Mountains of New Guinea.'),
      sp('ASTRAPIA_SPLENDIDISSIMA', 'Astrapia splendidissima', 'Splendid Astrapia', 'Astrapia', ['Oceania'], 0, 'A brilliantly coloured astrapia with metallic green and purple plumage, found in the central highlands of New Guinea.'),
      sp('ASTRAPIA_MAYERI', 'Astrapia mayeri', 'Ribbon-tailed Astrapia', 'Astrapia', ['Oceania'], 0, 'The most spectacular astrapia, with two extraordinarily long white tail streamers that can reach over one metre in length.'),
      sp('ASTRAPIA_ROTHSCHILDI', 'Astrapia rothschildi', 'Huon Astrapia', 'Astrapia', ['Oceania'], 0, 'An astrapia with iridescent green and blue plumage, restricted to the Huon Peninsula of New Guinea.')
    ]
  });

  // Add Drepanornis
  d.children.push({
    id: 'GENUS_DREPANORNIS', name: 'Drepanornis', rank: 'GENUS', commonName: 'Sicklebills',
    description: 'Medium-sized sicklebills with decurved bills and iridescent plumage.',
    lineage: 'Drepanornis',
    children: [
      sp('DREPANORNIS_BRUCIJNII', 'Drepanornis bruijnii', 'Pale-billed Sicklebill', 'Drepanornis', ['Oceania'], 0, 'A sicklebill with a pale, decurved bill and iridescent blue-green plumage, found in lowland forests of New Guinea.'),
      sp('DREPANORNIS_ALBERTISI', 'Drepanornis albertisi', 'Black-billed Sicklebill', 'Drepanornis', ['Oceania'], 0, 'A sicklebill with dark decurved bill and iridescent plumage, restricted to the montane forests of New Guinea.')
    ]
  });
}

// Quick function for remaining families - simplified additions
function expandSturnidae(d) {
  // Add Speculipastor
  d.children.push({
    id: 'GENUS_SPECULIPASTOR', name: 'Speculipastor', rank: 'GENUS', commonName: 'Magpie Starling',
    description: 'A striking black-and-white starling of arid East Africa with a long tail and pied plumage.',
    lineage: 'Starlings',
    children: [
      sp('SPECULIPASTOR_BICOLOR', 'Speculipastor bicolor', 'Magpie Starling', 'Starlings', ['Africa'], 0, 'A striking black-and-white starling of arid East Africa, its pied plumage unlike any other member of the family.')
    ]
  });
  // Add more species  
  if (!findGen(d, 'Saroglossa')) {
    d.children.push({
      id: 'GENUS_SAROGLOSSA', name: 'Saroglossa', rank: 'GENUS', commonName: 'Spot-winged Starling',
      description: 'An Asian genus of starling with distinctive spotted wing pattern.',
      lineage: 'Starlings',
      children: [
        sp('SAROGLOSSA_SPILOPTERA', 'Saroglossa spiloptera', 'Spot-winged Starling', 'Starlings', ['Asia'], 0, 'A medium-sized starling with rufous underparts and spotted wings, found from the Himalayas to Southeast Asia.')
      ]
    });
  }
  if (!findGen(d, 'Scissirostrum')) {
    d.children.push({
      id: 'GENUS_SCISSIROSTRUM', name: 'Scissirostrum', rank: 'GENUS', commonName: 'Finch-billed Starling',
      description: 'A monotypic Indonesian genus with heavy finch-like bill.',
      lineage: 'Starlings',
      children: [
        sp('SCISSIROSTRUM_DUBIUM', 'Scissirostrum dubium', 'Finch-billed Starling', 'Starlings', ['Asia'], 0, 'A starling endemic to Sulawesi with a stout conical bill unique among starlings.')
      ]
    });
  }
}

// Map families to their expander functions
const expanders = {
  'aves/passeriformes/petroicidae/src/data/petroicidae.json': expandPetroicidae,
  'aves/passeriformes/cotingidae/src/data/cotingidae.json': expandCotingidae,
  'aves/passeriformes/acanthizidae/src/data/acanthizidae.json': expandAcanthizidae,
  'aves/passeriformes/paradisaeidae/src/data/paradisaeidae.json': expandParadisaeidae,
  'aves/passeriformes/sturnidae/src/data/sturnidae.json': expandSturnidae,
};

// Process all families
Object.entries(expanders).forEach(([relPath, fn]) => {
  const fp = path.join(ROOT, relPath);
  if (fs.existsSync(fp)) {
    processFamily(relPath, fn);
  } else {
    console.log(`  SKIP ${relPath} - not found`);
  }
});
