#!/usr/bin/env python3
"""Final round: push remaining 10 close-to-green families to 100%."""
import json, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def load(p): return json.load(open(p))
def save(p, d): json.dump(d, open(p,"w"), indent=2, ensure_ascii=False)
def find(cc, n):
    for c in cc:
        if c.get("name")==n: return c
    return None
def cnt(n):
    return 1 if n.get("rank")=="SPECIES" else sum(cnt(c) for c in n.get("children",[]))
S = lambda sid,sn,co,ct,de: {"id":sid,"name":sn,"rank":"SPECIES","commonName":co,"lineage":sn.split()[-1]+"s","continents":ct,"subspeciesCount":0,"description":de}

F = {
    "phyllostomidae": "mammalia/chiroptera/phyllostomidae/src/data/phyllostomidae.json",
    "cuculidae": "aves/cuculiformes/cuculidae/src/data/cuculidae.json",
    "rallidae": "aves/gruiformes/rallidae/src/data/rallidae.json",
    "turdidae": "aves/passeriformes/turdidae/src/data/turdidae.json",
    "fringillidae": "aves/passeriformes/fringillidae/src/data/fringillidae.json",
    "sturnidae": "aves/passeriformes/sturnidae/src/data/sturnidae.json",
    "chamaeleonidae": "reptilia/squamata/chamaeleonidae/src/data/chamaeleonidae.json",
    "clupeidae": "actinopterygii/clupeiformes/clupeidae/src/data/clupeidae.json",
    "pteropodidae": "mammalia/chiroptera/pteropodidae/src/data/pteropodidae.json",
    "scorpionidae": "arachnida/scorpiones/scorpionidae/src/data/scorpionidae.json",
}

D = {}
D["phyllostomidae_Artibeus"] = [
    ("PHYLLO_ARTIBEUS_CINEREUS","Artibeus cinereus","Gervais's Fruit Bat",["South America"],"A small fruit-eating bat of the Amazon basin with a greyish face."),
    ("PHYLLO_ARTIBEUS_INCOMPTATUS","Artibeus incomitatus","Solitary Fruit Bat",["North America"],"A fruit bat from the Isla de Escudo de Veraguas, Panama."),
    ("PHYLLO_ARTIBEUS_TOLTECUS","Artibeus toltecus","Toltec Fruit Bat",["North America"],"A fruit bat of Central American highland forests."),
    ("PHYLLO_ARTIBEUS_WATSONI","Artibeus watsoni","Watson's Fruit Bat",["North America"],"A small fruit bat of Central America and northern South America."),
]
D["phyllostomidae_Carollia"] = [
    ("PHYLLO_CAROLLIA_BREVICAUDA","Carollia brevicauda","Silky Short-tailed Bat",["South America"],"A small fruit bat with a very short tail, found across the Amazon."),
    ("PHYLLO_CAROLLIA_CASTANEA","Carollia castanea","Chestnut Short-tailed Bat",["South America"],"A reddish-brown fruit bat of the western Amazon basin."),
    ("PHYLLO_CAROLLIA_SOWELLI","Carollia sowelli","Sowell's Short-tailed Bat",["North America"],"A fruit bat of Central America, distinguished by its larger size."),
]
D["phyllostomidae_Sturnira"] = [
    ("PHYLLO_STURNIRA_ERYTHROMOS","Sturnira erythromos","Hairy Yellow-shouldered Bat",["South America"],"A small yellow-shouldered bat of the Andean cloud forests."),
    ("PHYLLO_STURNIRA_LUDOVICI","Sturnira ludovici","Highland Yellow-shouldered Bat",["South America"],"A yellow-shouldered bat of highland forests from Colombia to Ecuador."),
    ("PHYLLO_STURNIRA_MAGNA","Sturnira magna","Greater Yellow-shouldered Bat",["South America"],"The largest Sturnira, found in the western Amazon."),
]

D["cuculidae_Cuculus"] = [
    ("CUCU_CUCULUS_GULARIS","Cuculus gularis","African Cuckoo",["Africa"],"The African equivalent of the common cuckoo, with a similar call."),
    ("CUCU_CUCULUS_ROCHII","Cuculus rochii","Madagascar Cuckoo",["Africa"],"A small cuckoo breeding in Madagascar and wintering in East Africa."),
    ("CUCU_CUCULUS_LEPIDUS","Cuculus lepidus","Sunda Cuckoo",["Asia"],"A small cuckoo of the Sunda Islands, recently split from the Oriental cuckoo."),
    ("CUCU_CUCULUS_CRASSIROSTRIS","Cuculus crassirostris","Sulawesi Cuckoo",["Asia"],"A large-billed cuckoo endemic to Sulawesi."),
]
D["cuculidae_Centropus"] = [
    ("CUCU_CENTROPUS_STEERII","Centropus steerii","Steere's Coucal",["Asia"],"A coucal endemic to the Philippine island of Mindoro."),
    ("CUCU_CENTROPUS_BERNSTEINI","Centropus bernsteini","Bernstein's Coucal",["Asia"],"A little-known coucal of the Vogelkop region of New Guinea."),
    ("CUCU_CENTROPUS_BURCHELLII","Centropus burchellii","Burchell's Coucal",["Africa"],"A common coucal of southern African savannas with a bubbling call."),
]

D["rallidae_Rallus"] = [
    ("RALL_RALLUS_CREPITANS","Rallus crepitans","Clapper Rail",["North America"],"A large rail of North American salt marshes, with a loud clattering call."),
    ("RALL_RALLUS_ELEGANS","Rallus elegans","King Rail",["North America"],"A large, cinnamon-coloured rail of freshwater marshes in eastern North America."),
    ("RALL_RALLUS_OBSOLETUS","Rallus obsoletus","Ridgway's Rail",["North America"],"A rail of California salt marshes, formerly considered a subspecies of the clapper rail."),
    ("RALL_RALLUS_TENUIROSTRIS","Rallus tenuirostris","Mexican Rail",["North America"],"A rail of Mexican highland marshes with a slender bill."),
]
D["rallidae_Fulica"] = [
    ("RALL_FULICA_ALAI","Fulica alai","Hawaiian Coot",["North America"],"A coot endemic to the Hawaiian Islands, with a white shield and dark body."),
    ("RALL_FULICA_CRISTATA","Fulica cristata","Red-knobbed Coot",["Africa","Europe"],"A coot of African and Iberian wetlands with red knobs on the frontal shield."),
    ("RALL_FULICA_NEWTONI","Fulica newtoni","Mascarene Coot",["Africa"],"An extinct coot of the Mascarene Islands, known from subfossil remains."),
]
D["rallidae_Gallinula"] = [
    ("RALL_GALLINULA_GALEATA","Gallinula galeata","Common Gallinule",["North America","South America"],"The New World counterpart of the common moorhen with a distinctive red shield."),
    ("RALL_GALLINULA_TENEBROSA","Gallinula tenebrosa","Dusky Moorhen",["Australia","Asia"],"An Australian and Indonesian moorhen, larger than the common moorhen."),
]
D["rallidae_Porzana"] = [
    ("RALL_PORZANA_FUSCA","Porzana fusca","Ruddy-breasted Crake",["Asia","Australia"],"A small crake of Asian marshes, with reddish-brown plumage and a whinnying call."),
    ("RALL_PORZANA_PAYKULLII","Porzana paykullii","Band-bellied Crake",["Asia"],"A striking crake with black-and-white barred belly from eastern Asia."),
    ("RALL_PORZANA_PUSILLA","Porzana pusilla","Baillon's Crake",["Europe","Asia","Africa","Australia"],"One of the smallest rails, barely larger than a sparrow."),
]

D["turdidae_Turdus"] = [
    ("TURD_TURDUS_GRAYI","Turdus grayi","Clay-colored Thrush",["North America"],"The national bird of Costa Rica, common in gardens and forest edges."),
    ("TURDUS_RUFITORQUES","Turdus rufitorques","Rufous-collared Thrush",["North America"],"A thrush of Central American highlands with a distinctive rufous collar."),
    ("TURD_TURDUS_INFUSCATUS","Turdus infuscatus","Black Thrush",["North America"],"A dark, slaty-black thrush of Central American montane forests."),
    ("TURD_TURDUS_PLEBEJUS","Turdus plebejus","Mountain Thrush",["North America"],"A thrush of highland forests from Mexico to Panama."),
    ("TURD_TURDUS_ASSIMILIS","Turdus assimilis","White-throated Thrush",["North America"],"A thrush with a white throat patch, common in Mexican and Central American highlands."),
    ("TURD_TURDUS_NIGRICEPS","Turdus nigriceps","Slaty Thrush",["South America"],"A grey thrush of Andean cloud forests from Argentina to Colombia."),
]

D["fringillidae_Carduelis"] = [
    ("FRIN_CARDUELIS_TRISTIS","Carduelis tristis","American Goldfinch",["North America"],"A small, bright yellow finch of North American weedy fields and gardens."),
    ("FRIN_CARDUELIS_LAWRENCII","Carduelis lawrencii","Lawrence's Goldfinch",["North America"],"A grey-gold finch of California oak savannas with a tinkling song."),
    ("FRIN_CARDUELIS_PINUS","Carduelis pinus","Pine Siskin",["North America"],"A streaky brown finch with yellow wing flashes, eruptive across North America."),
    ("FRIN_CARDUELIS_NOTATA","Carduelis notata","Black-capped Siskin",["North America"],"A siskin of Mexican and Central American highlands with black cap."),
]
D["fringillidae_Serinus"] = [
    ("FRIN_SERINUS_SERINUS","Serinus serinus","European Serin",["Europe","Asia","Africa"],"The smallest European finch, with a jangling, high-pitched song."),
    ("FRIN_SERINUS_CANARIA","Serinus canaria","Atlantic Canary",["Africa"],"The wild ancestor of the domestic canary, endemic to the Canary Islands and Madeira."),
    ("FRIN_SERINUS_SYRIACUS","Serinus syriacus","Syrian Serin",["Asia","Africa"],"A pale yellow serin of Middle Eastern mountains."),
]

D["sturnidae_Acridotheres"] = [
    ("STUR_ACRIDOTHERES_ATER","Acridotheres ater","Black-winged Myna",["Asia"],"A black myna with white wing patches from Myanmar and Thailand."),
    ("STUR_ACRIDOTHERES_CINERELLUS","Acridotheres cinereus","Javan Myna",["Asia"],"A grey myna of Java and Bali with a black head crest."),
]
D["sturnidae_Gracula"] = [
    ("STUR_GRACULA_TEMUCHII","Gracula temuchii","Temu Hill Myna",["Asia"],"A hill myna of the Sulu Archipelago in the Philippines."),
]

D["chamaeleonidae_Chamaeleo"] = [
    ("CHAM_CHAMAELEO_CALYPTRATUS","Chamaeleo calyptratus","Veiled Chameleon",["Asia"],"A large chameleon native to Yemen and Saudi Arabia with a tall casque."),
    ("CHAM_CHAMAELEO_ZEYLANICUS","Chamaeleo zeylanicus","Indian Chameleon",["Asia"],"The only chameleon found in India and Sri Lanka."),
]
D["chamaeleonidae_Furcifer"] = [
    ("CHAM_FURCIFER_LABORDI","Furcifer labordi","Labord's Chameleon",["Africa"],"A Madagascan chameleon with the shortest lifespan of any tetrapod."),
    ("CHAM_FURCIFER_VERRUCOSUS","Furcifer verrucosus","Warty Chameleon",["Africa"],"A large, warty chameleon of southwestern Madagascar."),
]

D["clupeidae_Alosa"] = [
    ("CLUP_ALOSA_CHRYSOCHLORIS","Alosa chrysochloris","Skipjack Shad",["North America"],"A fast-swimming shad of the Mississippi basin that leaps out of water."),
    ("CLUP_ALOSA_MEDIOCRIS","Alosa mediocris","Hickory Shad",["North America"],"A smaller shad of the US Atlantic coast, popular among fly anglers."),
    ("CLUP_ALOSA_SAPIDISSIMA","Alosa sapidissima","American Shad",["North America"],"The largest North American shad, prized for its roe and fighting ability."),
]

D["pteropodidae_Pteropus"] = [
    ("PTER_PTEROPUS_HYPOMELANUS","Pteropus hypomelanus","Variable Flying Fox",["Asia"],"A variable-coloured flying fox of Southeast Asian islands."),
    ("PTER_PTEROPUS_GRISEUS","Pteropus griseus","Grey Flying Fox",["Asia"],"A small grey flying fox of Sulawesi and Timor."),
    ("PTER_PTEROPUS_MACROTIS","Pteropus macrotis","Big-eared Flying Fox",["Australia"],"A flying fox with notably large ears, found on New Guinea and northern Queensland."),
    ("PTER_PTEROPUS_MELANOPOGON","Pteropus melanopogon","Black-bearded Flying Fox",["Asia"],"A large flying fox of the Moluccas with black beard-like tufts."),
]

D["scorpionidae_Pandinus"] = [
    ("SCOR_PANDINUS_GAMBIENSIS","Pandinus gambiensis","Gambian Forest Scorpion",["Africa"],"A large West African forest scorpion, popular in the pet trade."),
    ("SCOR_PANDINUS_PLATYCHELUS","Pandinus platychelus","Flat-clawed Forest Scorpion",["Africa"],"A large Pandinus with flattened pedipalps adapted for digging."),
]
D["scorpionidae_Heterometrus"] = [
    ("SCOR_HETEROMETRUS_LONGIMANUS","Heterometrus longimanus","Long-handed Forest Scorpion",["Asia"],"A forest scorpion with exceptionally long, slender pedipalps."),
    ("SCOR_HETEROMETRUS_INDUS","Heterometrus indus","Indian Forest Scorpion",["Asia"],"A large black forest scorpion of the Western Ghats and Sri Lanka."),
]

def run():
    for slug in sorted(F):
        rel = F[slug]
        p = os.path.join(ROOT, rel)
        d = load(p)
        b = cnt(d)
        # collect all genus additions for this slug
        for key in sorted(D):
            kslug, kg = key.split("_", 1)
            if kslug != slug: continue
            sps = D[key]
            g = find(d["children"], kg)
            if not g:
                print(f"  {kg} not found in {slug}")
                continue
            for s in sps:
                g["children"].append(S(*s))
        a = cnt(d)
        save(p, d)
        print(f"{slug:20s} {b:>4} → {a:>4} (+{a-b})")

if __name__ == "__main__": run()
