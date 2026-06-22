#!/usr/bin/env python3
"""Generate color themes and registry entries for new bird families."""
import json, re

with open('portal/src/colorRegistry.ts') as f:
    reg = f.read()

with open('portal/data/taxonomy.json') as f:
    t = json.load(f)

def find_aves(t):
    for phylum in t.get('children', []):
        for cc in phylum.get('children', []):
            if cc['id'] == 'AVES': return cc
aves = find_aves(t)

all_families = set()
for order in aves['children']:
    for family in order.get('children', []):
        all_families.add(family['appSlug'])

existing = set(m.group(1) for m in re.finditer(r'(\w+):\s+\w+_THEME', reg))
new_families = sorted(all_families - existing)

notable = {
    'struthionidae': '#807060', 'rheidae': '#a09878', 'apterygidae': '#8a7a58',
    'casuariidae': '#5a6850', 'tinamidae': '#a09070', 'anhimidae': '#687870',
    'anseranatidae': '#c0b8a0', 'megapodiidae': '#786050', 'cracidae': '#5a6840',
    'odontophoridae': '#a09860', 'podargidae': '#a08868', 'steatornithidae': '#d8c8a0',
    'nyctibiidae': '#a09878', 'aegothelidae': '#889078', 'hemiprocnidae': '#6878a0',
    'musophagidae': '#30a860', 'mesitornithidae': '#b09868', 'heliornithidae': '#687860',
    'sarothruridae': '#a07858', 'psophiidae': '#688898', 'aramidae': '#788878',
    'turnicidae': '#a09060', 'chionidae': '#d0d0d8', 'pluvianellidae': '#a0a8a0',
    'ibidorhynchidae': '#b0a090', 'pluvianidae': '#b0b8a0', 'rostratulidae': '#b09870',
    'pedionomidae': '#c0a870', 'thinocoridae': '#a0a878', 'dromadidae': '#d0c8b0',
    'rhynochetidae': '#789098', 'eurypygidae': '#a09848', 'phaethontidae': '#e8e8e0',
    'oceanitidae': '#485868', 'scopidae': '#8a7850', 'balaenicipitidae': '#788088',
    'opisthocomidae': '#a08848', 'coliidae': '#a09070', 'leptosomidae': '#7090a0',
    'trogonidae': '#20a060', 'phoeniculidae': '#2888a0', 'bucorvidae': '#484848',
    'bucerotidae': '#e8a820', 'brachypteraciidae': '#60a888', 'todidae': '#50b060',
    'momotidae': '#40a868', 'galbulidae': '#30a888', 'bucconidae': '#887058',
    'capitonidae': '#d86828', 'semnornithidae': '#c89830', 'lybiidae': '#c87020',
    'indicatoridae': '#889868', 'cariamidae': '#a09878', 'strigopidae': '#688868',
    'psittaculidae': '#20a060', 'artamidae': '#406090', 'maluridae': '#3880c0',
    'meliphagidae': '#789048', 'pomatostomidae': '#887060', 'petroicidae': '#d04828',
    'monarchidae': '#3878a8', 'rhipiduridae': '#688898', 'campephagidae': '#689098',
    'pachycephalidae': '#c89840', 'dicruridae': '#283848', 'ploceidae': '#c0a020',
    'zosteropidae': '#68a058', 'timaliidae': '#a07048', 'pellorneidae': '#887058',
    'leiothrichidae': '#d8a030', 'passerellidae': '#889070', 'calcariidae': '#a09870',
    'furnariidae': '#a07848', 'thamnophilidae': '#586060', 'pittidae': '#c84848',
    'pipridae': '#3858a0', 'cotingidae': '#c04840', 'grallariidae': '#887050',
    'rhinocryptidae': '#686058', 'eupetidae': '#5a6840', 'chaetopidae': '#789080',
    'picathartidae': '#d8c8a0', 'ifritidae': '#3868a8', 'corcoracidae': '#585850',
    'melampittidae': '#484040', 'tityridae': '#688898',
    'formicariidae': '#7a6850', 'conopophagidae': '#b09868',
    'melanopareiidae': '#a09060', 'sapayoidae': '#50a060',
    'philepittidae': '#60a028', 'calyptomenidae': '#30a840',
    'climacteridae': '#a07048', 'dasyornithidae': '#a08058',
    'pardalotidae': '#a8a050', 'acanthizidae': '#90a060',
    'orthonychidae': '#786850', 'cnemophilidae': '#88a040',
    'melanocharitidae': '#687050', 'paramythiidae': '#6090a8',
    'callaeidae': '#486868', 'notiomystidae': '#689898',
    'psophodidae': '#a09868', 'cinclosomatidae': '#7888a0',
    'platysteiridae': '#5880a0', 'malaconotidae': '#c87038',
    'machaerirhynchidae': '#c8a848', 'vangidae': '#60a088',
    'pityriasidae': '#483830', 'rhagologidae': '#a08860',
    'aegithinidae': '#c8a820', 'mohouidae': '#a09068',
    'neosittidae': '#788878', 'eulacestomatidae': '#a08048',
    'oreoicidae': '#888860', 'falcunculidae': '#a8a030',
    'platylophidae': '#506880', 'atrichornithidae': '#8a7860',
    'ptiliogonatidae': '#6070a0', 'hypocoliidae': '#a8a080',
    'dulidae': '#a08838', 'mohoidae': '#887860',
    'hylocitreidae': '#789068', 'stenostiridae': '#6090c0',
    'nicatoridae': '#789048', 'pnoepygidae': '#a88860',
    'macrosphenidae': '#98a068', 'cettiidae': '#a08858',
    'scotocercidae': '#a89878', 'erythrocercidae': '#d89838',
    'hyliidae': '#68a058', 'donacobiidae': '#706850',
    'bernieriidae': '#a0a068', 'paradoxornithidae': '#a08058',
    'alcippeidae': '#989068', 'modulatricidae': '#908070',
    'promeropidae': '#a09848', 'irenidae': '#2868a8',
    'elachuridae': '#8a7868', 'hyliotidae': '#7088a0',
    'tichodromidae': '#a09070', 'salpornithidae': '#8a7860',
    'buphagidae': '#c87030', 'chloropseidae': '#40a858',
    'dicaeidae': '#c06048', 'viduidae': '#384848',
    'peucedramidae': '#c8a828', 'urocynchramidae': '#a08868',
    'rhodinocichlidae': '#d07050', 'calyptophilidae': '#989068',
    'phaenicophilidae': '#68a058', 'nesospingidae': '#787860',
    'spindalidae': '#c8a028', 'zeledoniidae': '#687050',
    'teretistridae': '#c8a020', 'icteriidae': '#c8a820',
    'mitrospingidae': '#689868',
}

themes_code = []
for slug in new_families:
    color = notable.get(slug, '#889098')
    label = slug.title()
    themes_code.append(f'const {slug.upper()}_THEME: ColorTheme = {{ subfamilyColors: {{}}, lineageColors: {{ "{label}": "{color}" }}, breedGroupColor: "{color}", hybridColor: "#a8b0b8" }};')

registry_entries = []
for slug in new_families:
    padding = ' ' * max(1, 20 - len(slug))
    registry_entries.append(f'  {slug}:{padding}{slug.upper()}_THEME,')

print('# Theme constants to insert before COLUBRIDAE_THEME:')
print()
print('\n'.join(themes_code))
print()
print('# Registry entries to insert before colubridae:')
print()
print('\n'.join(registry_entries))
