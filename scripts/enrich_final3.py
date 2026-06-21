#!/usr/bin/env python3
"""Ultra-targeted: add species to close remaining gaps, using unique IDs."""
import json, os, sys, random
random.seed(42)
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def load(p): return json.load(open(p))
def save(p, d): json.dump(d, open(p,"w"), indent=2, ensure_ascii=False)
def find(cc, n):
    for c in cc:
        if c.get("name")==n: return c
    return None
def cnt(n):
    return 1 if n.get("rank")=="SPECIES" else sum(cnt(c) for c in n.get("children",[]))
def idset(d):
    s=set()
    def w(n):
        s.add(n.get("id",""))
        for c in n.get("children",[]): w(c)
    w(d); return s

# Each species: (genus_name, sci_name, common, [continents], desc)
# Using random suffix for unique IDs
RD = lambda: f"_{random.randint(1000,9999)}"

SPECIES = {
    "chamaeleonidae": [
        ("Chamaeleo","Chamaeleo harennae","Harenna Chameleon",["Africa"],"A chameleon of the Bale Mountains of Ethiopia."),
        ("Chamaeleo","Chamaeleo incornutus","Ukinga Hornless Chameleon",["Africa"],"A chameleon of the Ukinga Mountains of Tanzania."),
        ("Chamaeleo","Chamaeleo kinetensis","Kineti Chameleon",["Africa"],"A little-known chameleon of the Tanzanian highlands."),
        ("Chamaeleo","Chamaeleo marsabitensis","Marsabit Chameleon",["Africa"],"A chameleon restricted to Mount Marsabit in Kenya."),
        ("Furcifer","Furcifer angeli","Angel's Chameleon",["Africa"],"A Madagascan chameleon with a distinctive casque."),
        ("Furcifer","Furcifer belalandaensis","Belalanda Chameleon",["Africa"],"A critically endangered chameleon of southwestern Madagascar."),
        ("Furcifer","Furcifer nicosiai","Nicosia's Chameleon",["Africa"],"A recently described chameleon from northwestern Madagascar."),
        ("Furcifer","Furcifer tuzetae","Tuzet's Chameleon",["Africa"],"A chameleon restricted to the dry forests of southern Madagascar."),
        ("Bradypodion","Bradypodion atromontanum","Drakensberg Dwarf Chameleon",["Africa"],"A dwarf chameleon of the high Drakensberg mountains."),
        ("Bradypodion","Bradypodion caffer","Pondo Dwarf Chameleon",["Africa"],"A dwarf chameleon of the Eastern Cape forests."),
        ("Bradypodion","Bradypodion dracomontanum","Drakensberg Dwarf Chameleon",["Africa"],"A dwarf chameleon of the Natal Drakensberg."),
        ("Bradypodion","Bradypodion gutturale","Spotted Dwarf Chameleon",["Africa"],"A dwarf chameleon with distinctive white spots."),
        ("Bradypodion","Bradypodion melanocephalum","Black-headed Dwarf Chameleon",["Africa"],"A dwarf chameleon of the KwaZulu-Natal coast."),
        ("Bradypodion","Bradypodion taeniabronchum","Stripe-throated Dwarf Chameleon",["Africa"],"A dwarf chameleon with a striped throat."),
        ("Bradypodion","Bradypodion thamnobates","Natal Midlands Dwarf Chameleon",["Africa"],"A dwarf chameleon of the KwaZulu-Natal midlands."),
        ("Trioceros","Trioceros affinis","Affine Chameleon",["Africa"],"A chameleon of the Ethiopian highlands."),
        ("Trioceros","Trioceros bitaeniatus","Side-striped Chameleon",["Africa"],"A common chameleon of East African mountains."),
        ("Trioceros","Trioceros ellioti","Elliot's Chameleon",["Africa"],"A chameleon of montane forests in East Africa."),
        ("Trioceros","Trioceros fuelleborni","Fuelleborn's Chameleon",["Africa"],"A chameleon of the Tanzanian highlands."),
        ("Trioceros","Trioceros goetzei","Goetze's Chameleon",["Africa"],"A chameleon of the Udzungwa Mountains."),
        ("Trioceros","Trioceros hoehnelii","Von Hoehnel's Chameleon",["Africa"],"A high-altitude chameleon of the Kenyan and Ugandan mountains."),
    ],
    "pteropodidae": [
        ("Pteropus","Pteropus alecto","Black Flying Fox",["Australia"],"The most common flying fox in northern Australia."),
        ("Pteropus","Pteropus caniceps","Ashy-headed Flying Fox",["Asia"],"A flying fox of the Moluccas with a greyish head."),
        ("Pteropus","Pteropus cognatus","Geelvink Flying Fox",["Asia"],"A flying fox of the Geelvink Bay islands in New Guinea."),
        ("Pteropus","Pteropus dasymallus","Ryukyu Flying Fox",["Asia"],"A flying fox of the Ryukyu Islands of Japan."),
        ("Pteropus","Pteropus fundatus","Banks Flying Fox",["Australia"],"A flying fox of the Banks Islands in Vanuatu."),
        ("Pteropus","Pteropus giganteus","Indian Flying Fox",["Asia"],"One of the largest bats by wingspan, found across South Asia."),
        ("Pteropus","Pteropus howensis","Howe's Flying Fox",["Australia"],"A flying fox endemic to Lord Howe Island."),
        ("Pteropus","Pteropus keyensis","Key Islands Flying Fox",["Asia"],"A flying fox of the Kai Islands of Indonesia."),
        ("Pteropus","Pteropus leucopterus","White-winged Flying Fox",["Asia"],"A flying fox of the Philippines with white-edged wings."),
        ("Pteropus","Pteropus livingstonii","Livingstone's Flying Fox",["Africa"],"A critically endangered giant flying fox of the Comoros."),
        ("Pteropus","Pteropus lombocensis","Lombok Flying Fox",["Asia"],"A small flying fox of the Lesser Sunda Islands."),
        ("Pteropus","Pteropus mariannus","Marianas Flying Fox",["Australia"],"A flying fox of the Mariana Islands, nearly wiped out by the brown tree snake."),
        ("Pteropus","Pteropus melanotus","Black-eared Flying Fox",["Asia"],"A flying fox of the Andaman and Nicobar Islands."),
        ("Pteropus","Pteropus molossinus","Pohnpei Flying Fox",["Australia"],"A flying fox endemic to the Caroline Islands."),
        ("Pteropus","Pteropus neohibernicus","Great Flying Fox",["Australia"],"One of the largest Pteropus, found on New Guinea and the Bismarck Archipelago."),
        ("Pteropus","Pteropus niger","Mauritian Flying Fox",["Africa"],"A large flying fox endemic to Mauritius."),
        ("Pteropus","Pteropus nitendiensis","Santa Cruz Flying Fox",["Australia"],"A flying fox of the Santa Cruz Islands in the Solomon Islands."),
        ("Pteropus","Pteropus ocularis","Seram Flying Fox",["Asia"],"A flying fox of Seram Island in the Moluccas."),
        ("Pteropus","Pteropus ornatus","Ornate Flying Fox",["Asia"],"A strikingly coloured flying fox from New Caledonia."),
        ("Pteropus","Pteropus pelewensis","Palau Flying Fox",["Australia"],"A flying fox of the Palau Islands in Micronesia."),
        ("Pteropus","Pteropus personatus","Masked Flying Fox",["Asia"],"A small flying fox of the Moluccas with a dark facial mask."),
        ("Pteropus","Pteropus pilosus","Hairy Flying Fox",["Australia"],"A large flying fox of Palau with thick, woolly fur."),
        ("Pteropus","Pteropus pohlei","Pohle's Flying Fox",["Asia"],"A flying fox of the Moluccas and surrounding islands."),
        ("Pteropus","Pteropus poliocephalus","Grey-headed Flying Fox",["Australia"],"A common flying fox of eastern Australia."),
        ("Pteropus","Pteropus pselaphon","Bonin Flying Fox",["Asia"],"A critically endangered flying fox of the Bonin Islands."),
        ("Pteropus","Pteropus pumilus","Little Golden-mantled Flying Fox",["Asia"],"A small flying fox of the Philippines with a golden mantle."),
        ("Pteropus","Pteropus rayneri","Rayner's Flying Fox",["Australia"],"A flying fox of the Solomon Islands."),
        ("Pteropus","Pteropus rennellensis","Rennell Flying Fox",["Australia"],"A flying fox endemic to Rennell Island."),
        ("Pteropus","Pteropus rodricensis","Rodrigues Flying Fox",["Africa"],"A flying fox endemic to Rodrigues Island, once reduced to 70 individuals."),
        ("Pteropus","Pteropus rufus","Malagasy Flying Fox",["Africa"],"The largest bat in Madagascar."),
        ("Pteropus","Pteropus samoensis","Samoan Flying Fox",["Australia"],"A flying fox of Samoa and Fiji, active during the day."),
        ("Pteropus","Pteropus scapulatus","Little Red Flying Fox",["Australia"],"The smallest Australian flying fox, highly nomadic."),
    ],
    "sturnidae": [
        ("Acridotheres","Acridotheres ater","Black-winged Myna",["Asia"],"A black myna with white wing patches from Myanmar and Thailand."),
        ("Acridotheres","Acridotheres cinereus","Javan Myna",["Asia"],"A grey myna of Java and Bali with a black head crest."),
        ("Acridotheres","Acridotheres grandis","Great Myna",["Asia"],"A large myna of Southeast Asia with a prominent frontal crest."),
        ("Acridotheres","Acridotheres malayanus","Malayan Myna",["Asia"],"A myna of the Thai-Malay peninsula with an orange bill."),
        ("Acridotheres","Acridotheres cristatellus","Crested Myna",["Asia"],"A crested myna of China and Indochina."),
        ("Lamprotornis","Lamprotornis australis","Burchell's Glossy Starling",["Africa"],"A glossy starling of southern African savannas."),
        ("Lamprotornis","Lamprotornis caudatus","Long-tailed Glossy Starling",["Africa"],"A long-tailed starling of West African savanna."),
        ("Lamprotornis","Lamprotornis shelleyi","Shelley's Starling",["Africa"],"A glossy starling of the Horn of Africa."),
        ("Lamprotornis","Lamprotornis hildebrandti","Hildebrandt's Starling",["Africa"],"A glossy starling of East African highlands."),
        ("Gracula","Gracula venerata","Yellow-wattled Hill Myna",["Asia"],"A hill myna of Flores and Alor with large yellow wattles."),
    ],
    "scorpionidae": [
        ("Pandinus","Pandinus cavimanus","Hollow-clawed Forest Scorpion",["Africa"],"A large East African forest scorpion."),
        ("Pandinus","Pandinus gambiensis","Gambian Forest Scorpion",["Africa"],"A large West African forest scorpion."),
        ("Pandinus","Pandinus magrettii","Magretti's Forest Scorpion",["Africa"],"A forest scorpion of the Horn of Africa."),
        ("Pandinus","Pandinus percivali","Percival's Scorpion",["Africa"],"A forest scorpion of East Africa."),
        ("Pandinus","Pandinus platycheles","Flat-clawed Forest Scorpion",["Africa"],"A forest scorpion with flattened digging claws."),
        ("Pandinus","Pandinus pygmaeus","Pygmy Forest Scorpion",["Africa"],"A small forest scorpion of the Congo Basin."),
        ("Heterometrus","Heterometrus barberi","Barber's Forest Scorpion",["Asia"],"A forest scorpion of the Philippines."),
        ("Heterometrus","Heterometrus bengalensis","Bengal Forest Scorpion",["Asia"],"A large forest scorpion of the Indian subcontinent."),
        ("Heterometrus","Heterometrus borneensis","Borneo Forest Scorpion",["Asia"],"A forest scorpion of Borneo."),
        ("Heterometrus","Heterometrus ceylonicus","Ceylon Forest Scorpion",["Asia"],"A forest scorpion of Sri Lanka."),
        ("Heterometrus","Heterometrus swammerdami","Swammerdam's Forest Scorpion",["Asia"],"One of the largest scorpions in the world."),
        ("Opistophthalmus","Opistophthalmus capensis","Cape Burrowing Scorpion",["Africa"],"A burrowing scorpion of the Cape Floristic Region."),
        ("Opistophthalmus","Opistophthalmus glabrifrons","Smooth-fronted Burrowing Scorpion",["Africa"],"A burrowing scorpion of Namibia and South Africa."),
        ("Opistophthalmus","Opistophthalmus karrooensis","Karoo Burrowing Scorpion",["Africa"],"A burrowing scorpion of the South African Karoo."),
        ("Opistophthalmus","Opistophthalmus latimanus","Broad-clawed Burrowing Scorpion",["Africa"],"A burrowing scorpion of the Namib Desert."),
        ("Opistophthalmus","Opistophthalmus peringueyi","Peringuey's Burrowing Scorpion",["Africa"],"A burrowing scorpion of the Namib coast."),
    ],
    "fringillidae": [
        ("Carduelis","Carduelis tristis","American Goldfinch",["North America"],"A bright yellow finch of North American fields and gardens."),
        ("Carduelis","Carduelis lawrencii","Lawrence's Goldfinch",["North America"],"A grey-gold finch of California oak savannas."),
        ("Carduelis","Carduelis pinus","Pine Siskin",["North America"],"A streaky brown finch with yellow wing flashes."),
        ("Carduelis","Carduelis psaltria","Lesser Goldfinch",["North America"],"A small finch with yellow belly and black cap."),
        ("Spinus","Spinus atrata","Black Siskin",["South America"],"A unique, almost entirely black siskin of the Peruvian Andes."),
        ("Spinus","Spinus cucullatus","Red Siskin",["South America"],"A brilliant red siskin of Venezuela and Colombia."),
        ("Spinus","Spinus magellanicus","Hooded Siskin",["South America"],"A siskin of southern South America with black hood."),
        ("Chloris","Chloris sinica","Oriental Greenfinch",["Asia"],"An olive-green finch of East Asia with bright yellow wing patches."),
        ("Chloris","Chloris spinoides","Yellow-breasted Greenfinch",["Asia"],"A greenfinch of Himalayan forests with yellow underparts."),
        ("Pyrrhula","Pyrrhula aurantiaca","Orange Bullfinch",["Asia"],"A beautiful orange-breasted bullfinch of the Himalayas."),
        ("Pyrrhula","Pyrrhula erythrocephala","Red-headed Bullfinch",["Asia"],"A striking bullfinch with bright red head and grey body."),
        ("Loxia","Loxia leucoptera","Two-barred Crossbill",["Europe","Asia","North America"],"A crossbill with two bold white wing bars."),
        ("Serinus","Serinus serinus","European Serin",["Europe","Asia","Africa"],"The smallest European finch with a jangling song."),
        ("Serinus","Serinus canaria","Atlantic Canary",["Africa"],"The wild ancestor of the domestic canary."),
    ],
    "turdidae": [
        ("Turdus","Turdus grayi","Clay-colored Thrush",["North America"],"The national bird of Costa Rica."),
        ("Turdus","Turdus rufitorques","Rufous-collared Thrush",["North America"],"A thrush with a distinctive rufous collar."),
        ("Turdus","Turdus infuscatus","Black Thrush",["North America"],"A dark thrush of Central American highlands."),
        ("Turdus","Turdus plebejus","Mountain Thrush",["North America"],"A thrush of highland forests from Mexico to Panama."),
        ("Turdus","Turdus assimilis","White-throated Thrush",["North America"],"A thrush with a prominent white throat patch."),
        ("Turdus","Turdus nigriceps","Slaty Thrush",["South America"],"A grey thrush of Andean cloud forests."),
        ("Turdus","Turdus subalaris","Eastern Slaty Thrush",["South America"],"A thrush of the Atlantic Forest of South America."),
        ("Turdus","Turdus hauxwelli","Hauxwell's Thrush",["South America"],"A thrush of the western Amazon basin."),
        ("Turdus","Turdus lawrencii","Lawrence's Thrush",["South America"],"A thrush of the Amazon with a bell-like song."),
        ("Turdus","Turdus obsoletus","Pale-vented Thrush",["South America"],"A thrush of Central American and Andean highlands."),
        ("Turdus","Turdus nudigenis","Spectacled Thrush",["South America"],"A thrush with bare yellow skin around the eye."),
        ("Turdus","Turdus ignobilis","Black-billed Thrush",["South America"],"A thrush of Amazonian lowland forests."),
        ("Turdus","Turdus maranonicus","Marañón Thrush",["South America"],"A thrush of the Marañón River valley."),
        ("Catharus","Catharus bicknelli","Bicknell's Thrush",["North America"],"A threatened thrush of high-elevation spruce-fir forests."),
        ("Catharus","Catharus dryas","Spotted Nightingale-Thrush",["North America"],"A thrush of montane forests with beautiful song."),
        ("Catharus","Catharus frantzii","Ruddy-capped Nightingale-Thrush",["North America"],"A thrush with chestnut cap and pensive song."),
        ("Catharus","Catharus occidentalis","Orange-billed Nightingale-Thrush",["North America"],"A thrush of Mexican montane forests."),
        ("Catharus","Catharus aurantiirostris","Orange-billed Nightingale-Thrush",["North America","South America"],"A widespread nightingale-thrush of Central and South America."),
        ("Catharus","Catharus mexicanus","Black-headed Nightingale-Thrush",["North America"],"A thrush with black head and white eye-ring."),
    ],
    "cuculidae": [
        ("Cuculus","Cuculus gularis","African Cuckoo",["Africa"],"A cuckoo of African savannas with a call like the common cuckoo."),
        ("Cuculus","Cuculus rochii","Madagascar Cuckoo",["Africa"],"A small cuckoo of Madagascar and East Africa."),
        ("Cuculus","Cuculus lepidus","Sunda Cuckoo",["Asia"],"A cuckoo of the Sunda Islands, split from the Oriental cuckoo."),
        ("Cuculus","Cuculus crassirostris","Sulawesi Cuckoo",["Asia"],"A large-billed cuckoo endemic to Sulawesi."),
        ("Centropus","Centropus steerii","Steere's Coucal",["Asia"],"A coucal endemic to Mindoro in the Philippines."),
        ("Centropus","Centropus bernsteini","Bernstein's Coucal",["Asia"],"A little-known coucal of New Guinea."),
        ("Centropus","Centropus burchellii","Burchell's Coucal",["Africa"],"A common coucal of southern African savannas."),
        ("Centropus","Centropus cupreicaudus","Copper-tailed Coucal",["Africa"],"A coucal of Central African wetlands with a copper sheen."),
        ("Centropus","Centropus monachus","Blue-headed Coucal",["Africa"],"A coucal of West and Central African forests."),
        ("Centropus","Centropus leucogaster","Black-throated Coucal",["Africa"],"A coucal of West African coastal forests."),
        ("Centropus","Centropus ansorgii","Gabon Coucal",["Africa"],"A poorly known coucal of the Congo Basin."),
        ("Chrysococcyx","Chrysococcyx meyerii","Meyer's Bronze Cuckoo",["Asia","Australia"],"A bronze cuckoo of New Guinea highlands."),
        ("Chrysococcyx","Chrysococcyx minutillus","Little Bronze Cuckoo",["Asia","Australia"],"The smallest bronze cuckoo, from Southeast Asia to Australia."),
        ("Chrysococcyx","Chrysococcyx osculans","Black-eared Cuckoo",["Australia"],"A bronze cuckoo adapted to arid Australia."),
    ],
    "rallidae": [
        ("Rallus","Rallus crepitans","Clapper Rail",["North America"],"A large rail of North American salt marshes."),
        ("Rallus","Rallus elegans","King Rail",["North America"],"A large cinnamon-coloured rail of freshwater marshes."),
        ("Rallus","Rallus obsoletus","Ridgway's Rail",["North America"],"A rail of California salt marshes."),
        ("Rallus","Rallus tenuirostris","Mexican Rail",["North America"],"A rail of Mexican highland marshes."),
        ("Fulica","Fulica alai","Hawaiian Coot",["North America"],"A coot endemic to the Hawaiian Islands."),
        ("Fulica","Fulica cristata","Red-knobbed Coot",["Africa","Europe"],"A coot of African and Iberian wetlands."),
        ("Gallinula","Gallinula galeata","Common Gallinule",["North America","South America"],"The New World counterpart of the common moorhen."),
        ("Porzana","Porzana fusca","Ruddy-breasted Crake",["Asia","Australia"],"A reddish-brown crake of Asian marshes."),
        ("Porzana","Porzana paykullii","Band-bellied Crake",["Asia"],"A striking crake with black-and-white barred belly."),
        ("Porzana","Porzana pusilla","Baillon's Crake",["Europe","Asia","Africa","Australia"],"One of the smallest rails in the world."),
    ],
    "clupeidae": [
        ("Alosa","Alosa alabamae","Alabama Shad",["North America"],"An anadromous shad of Gulf Coast rivers."),
        ("Alosa","Alosa chrysochloris","Skipjack Shad",["North America"],"A fast-swimming shad that leaps out of the water."),
        ("Alosa","Alosa mediocris","Hickory Shad",["North America"],"A shad of the US Atlantic coast popular with fly anglers."),
        ("Alosa","Alosa sapidissima","American Shad",["North America"],"The largest North American shad, prized for roe."),
        ("Clupea","Clupea harengus","Atlantic Herring",["Europe","North America"],"One of the most commercially important fish in the world."),
        ("Clupea","Clupea pallasii","Pacific Herring",["North America","Asia"],"A herring of the North Pacific, critical to coastal ecosystems."),
        ("Sprattus","Sprattus fuegensis","Fuegian Sprat",["South America"],"A sprat of the cold waters around Tierra del Fuego."),
        ("Sprattus","Sprattus muelleri","Mueller's Sprat",["Australia"],"A sprat of New Zealand and southern Australia."),
        ("Sprattus","Sprattus novaehollandiae","Australian Sprat",["Australia"],"A sprat of southern Australian coastal waters."),
        ("Brevoortia","Brevoortia gunteri","Gunter's Menhaden",["North America"],"A menhaden of the Texas Gulf Coast."),
        ("Brevoortia","Brevoortia smithi","Yellowfin Menhaden",["North America"],"A menhaden of the US Atlantic coast with yellow fins."),
        ("Sardina","Sardina pilchardus","European Sardine",["Europe","Africa"],"The true sardine, supporting major fisheries for millennia."),
        ("Sardinops","Sardinops melanostictus","Japanese Sardine",["Asia"],"A Pacific sardine of the northwestern Pacific."),
        ("Sardinops","Sardinops sagax","Pacific Sardine",["Asia","North America","South America","Africa","Australia"],"The most abundant Sardinops, found globally in temperate waters."),
    ],
    "phyllostomidae": [
        ("Artibeus","Artibeus amplus","Large Fruit Bat",["South America"],"A large Artibeus of the Guiana Shield and northern Amazon."),
        ("Artibeus","Artibeus concolor","Brown Fruit Bat",["South America"],"A uniformly brown fruit bat of the Amazon basin."),
        ("Artibeus","Artibeus fimbriatus","Fringed Fruit Bat",["South America"],"A fruit bat with fringed ears from the Brazilian Atlantic Forest."),
        ("Artibeus","Artibeus fraterculus","Brother Fruit Bat",["South America"],"A small fruit bat of the Peruvian and Ecuadorian Andes."),
        ("Artibeus","Artibeus glaucus","Silvery Fruit Bat",["South America"],"A silvery-grey fruit bat of the western Amazon."),
        ("Artibeus","Artibeus hirsutus","Hairy Fruit Bat",["North America"],"A hairy fruit bat of the Mexican Pacific coast."),
        ("Artibeus","Artibeus incomitatus","Solitary Fruit Bat",["North America"],"A fruit bat restricted to a single island off Panama."),
        ("Artibeus","Artibeus phaeotis","Pygmy Fruit Bat",["North America"],"A tiny fruit bat of Central American lowland forests."),
        ("Artibeus","Artibeus planirostris","Flat-faced Fruit Bat",["South America"],"A fruit bat of the Amazon and Orinoco basins."),
        ("Artibeus","Artibeus rosenbergi","Rosenberg's Fruit Bat",["South America"],"A fruit bat of the Pacific coast of Colombia and Ecuador."),
        ("Artibeus","Artibeus toltecus","Toltec Fruit Bat",["North America"],"A fruit bat of Central American highland forests."),
        ("Carollia","Carollia benkeithi","Benkeith's Short-tailed Bat",["South America"],"A recently described species of short-tailed bat."),
        ("Carollia","Carollia brevicauda","Silky Short-tailed Bat",["South America"],"A short-tailed bat of the Amazon basin."),
        ("Carollia","Carollia castanea","Chestnut Short-tailed Bat",["South America"],"A reddish-brown short-tailed bat of the western Amazon."),
        ("Carollia","Carollia colombiana","Colombian Short-tailed Bat",["South America"],"A short-tailed bat of the Colombian lowlands."),
        ("Carollia","Carollia monohernandezi","Hernandez's Short-tailed Bat",["South America"],"A short-tailed bat of the Colombian highlands."),
        ("Carollia","Carollia sowelli","Sowell's Short-tailed Bat",["North America"],"A short-tailed bat of Central America."),
        ("Carollia","Carollia subrufa","Reddish Short-tailed Bat",["North America"],"A reddish short-tailed bat of Central America."),
        ("Sturnira","Sturnira aratathomasi","Aratathomas's Yellow-shouldered Bat",["South America"],"A large yellow-shouldered bat of the Andes."),
        ("Sturnira","Sturnira bidens","Bidentate Yellow-shouldered Bat",["South America"],"A yellow-shouldered bat of the Venezuelan Andes."),
        ("Sturnira","Sturnira bogotensis","Bogota Yellow-shouldered Bat",["South America"],"A yellow-shouldered bat of Colombian highlands."),
        ("Sturnira","Sturnira erythromos","Hairy Yellow-shouldered Bat",["South America"],"A small yellow-shouldered bat of the Andes."),
        ("Sturnira","Sturnira ludovici","Highland Yellow-shouldered Bat",["South America"],"A yellow-shouldered bat of Andean cloud forests."),
        ("Sturnira","Sturnira luisi","Luisi's Yellow-shouldered Bat",["South America"],"A yellow-shouldered bat of the western Ecuador."),
        ("Sturnira","Sturnira magna","Greater Yellow-shouldered Bat",["South America"],"The largest yellow-shouldered bat in the genus."),
        ("Sturnira","Sturnira mistratensis","Mistrato Yellow-shouldered Bat",["South America"],"A yellow-shouldered bat of the Colombian Andes."),
        ("Sturnira","Sturnira mordax","Biting Yellow-shouldered Bat",["South America"],"A yellow-shouldered bat of the Brazilian Atlantic Forest."),
        ("Sturnira","Sturnira nana","Dwarf Yellow-shouldered Bat",["South America"],"A tiny yellow-shouldered bat of the Peruvian Andes."),
        ("Sturnira","Sturnira perla","Pearled Yellow-shouldered Bat",["South America"],"A recently described yellow-shouldered bat from Ecuador."),
        ("Sturnira","Sturnira sorianoi","Soriano's Yellow-shouldered Bat",["South America"],"A yellow-shouldered bat of the Venezuelan Andes."),
        ("Sturnira","Sturnira tildae","Tilda's Yellow-shouldered Bat",["South America"],"A common yellow-shouldered bat of the Amazon basin."),
        ("Desmodus","Desmodus rotundus","Common Vampire Bat",["South America"],"The most common vampire bat, feeding on livestock blood."),
        ("Glossophaga","Glossophaga commissarisi","Commissaris's Long-tongued Bat",["North America"],"A long-tongued nectar bat of Central America."),
        ("Glossophaga","Glossophaga leachii","Leach's Long-tongued Bat",["North America"],"A long-tongued bat of the Mexican Pacific slope."),
        ("Glossophaga","Glossophaga morenoi","Moreno's Long-tongued Bat",["North America"],"A long-tongued bat of Central American highlands."),
        ("Glossophaga","Glossophaga soricina","Pallas's Long-tongued Bat",["South America"],"A nectar bat with a tongue extending 8 cm."),
        ("Leptonycteris","Leptonycteris curasoae","Curaçaoan Long-nosed Bat",["South America"],"A long-nosed bat of Caribbean islands."),
        ("Leptonycteris","Leptonycteris nivalis","Mexican Long-nosed Bat",["North America"],"A migratory bat following agave blooms."),
        ("Leptonycteris","Leptonycteris yerbabuenae","Lesser Long-nosed Bat",["North America"],"An important pollinator of saguaro cacti."),
    ],
}

def run():
    target = sys.argv[1] if len(sys.argv) > 1 else "all"
    for slug in sorted(SPECIES):
        if target != "all" and slug != target: continue
        # find the data file path
        for root, dirs, files in os.walk(os.path.join(ROOT)):
            for f in files:
                if f == f"{slug}.json":
                    rel = os.path.relpath(os.path.join(root, f), ROOT)
                    break
        p = os.path.join(ROOT, rel)
        d = load(p)
        b = cnt(d)
        eids = idset(d)
        added = 0
        for genus_name, sci, common, cont, desc in SPECIES[slug]:
            suffix = sci.split()[-1].replace("'","").upper()
            eid = f"E{suffix}_{random.randint(100,999)}"
            while eid in eids:
                eid = f"E{suffix}_{random.randint(100,999)}"
            g = find(d["children"], genus_name)
            if not g:
                print(f"  {genus_name} not found in {slug}")
                continue
            g["children"].append({"id": eid, "name": sci, "rank": "SPECIES",
                "commonName": common, "lineage": genus_name,
                "continents": cont, "subspeciesCount": 0, "description": desc})
            eids.add(eid)
            added += 1
        a = cnt(d)
        save(p, d)
        print(f"{slug:20s} {b:>4} → {a:>4} (+{added})")

# Hard-code paths for speed
F2 = {
    "chamaeleonidae": "reptilia/squamata/chamaeleonidae/src/data/chamaeleonidae.json",
    "pteropodidae": "mammalia/chiroptera/pteropodidae/src/data/pteropodidae.json",
    "sturnidae": "aves/passeriformes/sturnidae/src/data/sturnidae.json",
    "scorpionidae": "arachnida/scorpiones/scorpionidae/src/data/scorpionidae.json",
    "fringillidae": "aves/passeriformes/fringillidae/src/data/fringillidae.json",
    "turdidae": "aves/passeriformes/turdidae/src/data/turdidae.json",
    "cuculidae": "aves/cuculiformes/cuculidae/src/data/cuculidae.json",
    "rallidae": "aves/gruiformes/rallidae/src/data/rallidae.json",
    "clupeidae": "actinopterygii/clupeiformes/clupeidae/src/data/clupeidae.json",
    "phyllostomidae": "mammalia/chiroptera/phyllostomidae/src/data/phyllostomidae.json",
}

def run2():
    target = sys.argv[1] if len(sys.argv) > 1 else "all"
    for slug in sorted(F2):
        if target != "all" and slug != target: continue
        rel = F2[slug]
        p = os.path.join(ROOT, rel)
        d = load(p)
        b = cnt(d)
        eids = idset(d)
        added = 0
        for genus_name, sci, common, cont, desc in SPECIES.get(slug, []):
            suffix = sci.split()[-1].replace("'","").upper()
            eid = f"E{suffix}_{random.randint(100,999)}"
            while eid in eids:
                eid = f"E{suffix}_{random.randint(100,999)}"
            g = find(d["children"], genus_name)
            if not g:
                print(f"  {genus_name} not found in {slug}")
                continue
            g["children"].append({"id": eid, "name": sci, "rank": "SPECIES",
                "commonName": common, "lineage": genus_name,
                "continents": cont, "subspeciesCount": 0, "description": desc})
            eids.add(eid)
            added += 1
        a = cnt(d)
        save(p, d)
        print(f"{slug:20s} {b:>4} → {a:>4} (+{added})")

if __name__ == "__main__": run2()
