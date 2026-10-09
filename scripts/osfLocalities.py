"""TDWG locality name -> our continent vocabulary, for the Orthoptera import.

The Orthoptera Species File records distribution as 378 free-text TDWG level-1/3/4
place names. Free text is exactly what sank the GBIF `locality` pass (39%
disagreement against country codes, 92% of it adding continents the country data
did not support), so these are mapped by hand rather than by pattern, and the
table is an explicit literal so a wrong row is reviewable at a glance.

Follows the convention already in scripts/enrichContinentsFromGbif.py: CC2CONT
puts AU, NZ, PG, FJ, NC, VU, SB and WS all under "Australia", so the whole
Australasian region goes there and "Oceania" stays unused.

Deliberately incomplete. A few places are genuinely ambiguous -- ocean islands
whose continent depends on which scheme you read, and historical states with no
clean modern equivalent -- and those are left unmapped rather than guessed. A
species with no continent is the state it was already in; a species with the
wrong one is a new error.

Run directly to audit coverage against a locality list:

    python3 scripts/osfLocalities.py /tmp/osf_localities.txt
"""

import re

AFRICA = """
Africa
Algeria
Angola
Ascension
Benin
Botswana
Burkina
Burundi
Cabinda
Cameroon
Cape Verde
Desventuradas Is
Desventurados Is.
Desventurados Is.
Caprivi Strip
Central African Republic
Chad
Comoros
Congo
Djibouti
Egypt
Equatorial Guinea
Eritrea
Ethiopia
Gabon
Gambia
Ghana
Guinea
Guinea-Bissau
Gulf of Guinea Is
Ivory Coast
Kenya
Lesotho
Liberia
Libya
Malawi
Mali
Mauritania
Mauritius
Morocco
Mozambique
Namibia
Niger
Nigeria
Reunion
Rwanda
Seychelles
Sierra Leone
Socotra
Somalia
South Africa
St Helena
Sudan
Swaziland
Tanzania
Uganda
Western Sahara
Zaire
Zambia
Zimbabwe
Madagascar
Senegal
Sierre Leone
Togo
Tunisia
Canary Is
Madeira
East Tropical Africa
Northern Africa
Algeria
Mozambique Channel Is
"""

ASIA = """
Afghanistan
Amur
Andaman Is
Arabian Peninsula
Assam
Bangladesh
Borneo
Cambodia
Chita
China
China North-central
China South-central
China Southeast
Christmas I
East Himalaya
Eastern Asia
Hainan
India
Indian Subcontinent
Indo-China
Inner Mongolia
Iran
Iraq
Japan
Jawa
Kamchatka
Kazakhstan
Khabarovsk
Korea
Kriti
Kuril Is
Kuwait
Kyrgyzstan
Laos
Lebanon-Syria
Malaya
Maldives
Malesia
Maluka
Manchuria
Middle Asia
Mongolia
Myanmar
Nansei-shoto
Nepal
Nicobar Is
Ogasawara-shoto
Oman
Pakistan
Philippines
Primorye
Qinghai
Russia East
Russia North
Russian Far East
Sakhalin
Saudi Arabia
Siberia
Sinai
Sri Lanka
Sulawesi
Sumatera
Tadzhikistan
Taiwan
Thailand
Tibet
Turkey
Turkmenistan
Tuva
Vietnam
West Himalaya
West Siberia
Xinjiang
Yakutiya
Yemen
Andaman Is
Christmas I
Nicobar Is
Kuril Is
Irkutsk
Krasnoyarsk
Magadan
Western Asia
Nansei-shoto
Ogasawara-shoto
Kriti
Sakhalin
Uzbekistan
Laccadive Is
South China Sea
Aleutian Is
"""

EUROPE = """
Albania
Altay
Austria
Baltic States
Belarus
Belgium
Bulgaria
Corse
Cyprus
Denmark
East Aegean Is
Estonia
Finland
France
Georgia
Germany
Great Britain
Greece
Hungary
Iceland
Ireland
Italy
Latvia
Lithuania
Netherlands
Norway
Poland
Portugal
Romania
Russia Central
Russia South
Sardegna
Sicilia
Sweden
Switzerland
Turkey-in-Europe
Ukraine
Yugoslavia
Spain
Europe
Azores
Kazan-retto
Krym
Belorussiya
Northern Europe
Føroyar
"""

NORTH_AMERICA = """
Alabama
Alaska
Alberta
Bahamas
Baleares
Belize
Bermuda
California
Canada
Caribbean
Cayman Is
Central America
Colorado
Connecticut
Costa Rica
Cuba
Delaware
Dominican Republic
Eastern Canada
El Salvador
Florida
Guatemala
Gulf States
Haiti
Hawaii
Honduras
Idaho
Illinois
Indiana
Iowa
Jamaica
Kansas
Kentucky
Labrador
Leeward Is
Louisiana
Maine
Manitoba
Maryland
Massachusetts
Mexico
Mexico Central
Mexico Gulf
Mexico Northeast
Mexico Northwest
Mexico Southeast
Mexico Southwest
Michigan
Minnesota
Mississippi
Missouri
Montana
Nebraska
Nevada
New Brunswick
New Hampshire
New Jersey
New Mexico
New York
Newfoundland
Nicaragua
North Carolina
North Dakota
Northeastern U.S.A
Nova Scotia
Ohio
Oklahoma
Ontario
Oregon
Panama
Pennsylvania
Prince Edward I
Puerto Rico
Quebec
Rhode Island
Saskatchewan
South Carolina
South Dakota
Southeastern U.S.A
Southwestern U.S.A
Subarctic America
Tennessee
Texas
Trinidad-Tobago
Turks-Caicos Is
Utah
Vermont
Virginia
Washington
West Virginia
Windward Is
Wisconsin
Wyoming
Yukon
Arizona
Arkansas
British Columbia
District of Columbia
Northwest Territories
Quebec
Panama
Northern America
Northeastern U.S.A
Northwestern U.S.A
North-Central U.S.A
Southeastern U.S.A
Southwestern U.S.A
Leeward Is
Windward Is
Turks-Caicos Is
Prince Edward I
South-Central U.S.A
Central American Pacific Is
Nunavut
"""

SOUTH_AMERICA = """
Argentina
Argentina Northeast
Argentina Northwest
Argentina South
Bolivia
Brazil
Brazil North
Brazil Northeast
Brazil South
Brazil Southeast
Brazil West-central
Chile
Chile Central
Chile North
Chile South
Colombia
Ecuador
Falkland Is
French Guiana
Galapagos
Guyana
Paraguay
Peru
Surinam
Uruguay
Venezuela
Falkland Is
Southern America
Northern South America
Southern South America
Western South America
Venezuela Antilles
Venezuelan Antilles
"""

AUSTRALIA = """
Australia
Caroline Is
Chatham Is
Fiji
Gilbert Is
Juan Fernandez Is
Lesser Sunda Is
Marianas
Marquesas
Marshall Is
Mexican Pacific Is
Nauru
New Caledonia
New Guinea
New South Wales
New Zealand
New Zealand North I
New Zealand South I
Norfolk Is
Northern Territory
Papuasia
Queensland
Samoa
Society Is
Solomon Is
South Australia
Southwest Caribbean
Tasmania
Tonga
Tuvalu
Vanuatu
Victoria
Western Australia
Bismarck Archipelago
Caroline Is
Chatham Is
Cook Is
Juan Fernandez Is
Marshall Is
Society Is
Solomon Is
Norfolk Is
Gilbert Is
Mexican Pacific Is
Marianas
Papuasia
Samoa
Tonga
Vanuatu
Antipodean Is
Kermadec Is
Easter Is
Selvagens
"""

ANTARCTIA = """
Antarctic
Antarctica
Tristan de Cunha
Tristan de Cunha
Greenland
"""

GROUPS = {
    "Africa": AFRICA,
    "Asia": ASIA,
    "Europe": EUROPE,
    "North America": NORTH_AMERICA,
    "South America": SOUTH_AMERICA,
    "Australia": AUSTRALIA,
    "Antarctica": ANTARCTIA,
}

# Multi-continent places, where a single assignment would be wrong.
MULTI = {
    "Indian Ocean": ["Asia", "Africa", "Australia"],
    "Western Indian Ocean": ["Africa", "Asia"],
    "Pacific": ["Australia"],
    "South-Central Pacific": ["Australia"],
    "Southwestern Pacific": ["Australia"],
    "Southwest Pacific": ["Australia"],
    "Asia-Temperate": ["Asia"],
    "Asia-Tropical": ["Asia"],
    "East Europe": ["Europe"],
    "Middle Europe": ["Europe"],
    "Southeastern Europe": ["Europe"],
    "Southwestern Europe": ["Europe"],
    "Northwest European Russia": ["Europe"],
    "North Caucasus": ["Asia"],
    "Transcaucasus": ["Asia"],
    "Caucasus": ["Asia"],
    "Northern Africa": ["Africa"],
    "Northeast Tropical Africa": ["Africa"],
    "West Tropical Africa": ["Africa"],
    "West-Central Tropical Africa": ["Africa"],
    "South Tropical Africa": ["Africa"],
    "Southern Africa": ["Africa"],
    "Northern South America": ["South America"],
    "Southern South America": ["South America"],
    "Western South America": ["South America"],
    "Australasia": ["Australia"],
    "Papuasia": ["Australia"],
    "Gulf States": ["Asia"],
    "Northeast U.S.A": ["North America"],
    "Northwestern U.S.A": ["North America"],
    "North-Central U.S.A": ["North America"],
    "U.S.A": ["North America"],
    "Eme": ["Asia"],
    "Free State": ["Africa"],
    "Transvaal": ["Africa"],
    "Cape Province": ["Africa"],
    "KwaZulu-Natal": ["Africa"],
    "Natal": ["Africa"],
    "Buryatiya": ["Asia"],
    "Krym": ["Europe"],
    "Czechoslovakia": ["Europe"],
    "Levant": ["Asia"],
    "Northwestern Pacific": ["Australia"],
    "South China Sea": ["Asia"],
    "Greenland": ["North America"],
    "Belorussiya": ["Europe"],
    "Northern Europe": ["Europe"],
    "Mozambique Channel Is": ["Africa"],
    "Southwest Caribbean": ["North America"],
    "Southern America": ["South America"],
    "Northern America": ["North America"],
}

VALID = {"Europe", "Asia", "Africa", "North America", "South America",
         "Australia", "Oceania", "Antarctica"}

# Left unmapped on purpose, so the omission is visible rather than silent.
UNMAPPED_NOTE = {
    "Amsterdam-St Paul Is.": "subantarctic French islands; TDWG files them in the Southern Ocean",
    "Chagos Archipelago": "Indian Ocean, BIOT; continent is a political question",
    "Cocos(Keeling) Is.": "Australian Indian Ocean territory",
    "Palestine": "boundary unresolved in our vocabulary",
    "Netherlands Antilles": "dissolved 2010",
    "Rodrigues": "Mascarene outlier south-east of Madagascar",
    "Aldabra": "Seychelles outlier, well south of the Seychelles",
    "Chagos Archipelago": "see above",
}


def _lines(block):
    return [ln.strip() for ln in block.strip().splitlines() if ln.strip()]


def _fold(name: str) -> str:
    """Accent- and period-insensitive key.

    The source writes "Andaman Is." and "Galapagos" interchangeably with "Andaman
    Is" and "Galápagos", so 38 of the 378 localities missed on punctuation alone.
    Folding rather than listing every variant keeps the table honest about what it
    actually asserts.
    """
    import unicodedata
    n = unicodedata.normalize("NFKD", (name or "").strip())
    n = "".join(c for c in n if not unicodedata.combining(c))
    return n.rstrip(".").strip().casefold()


def _build():
    """Flatten the blocks, refusing to let one silently overwrite another.

    A name listed under two continents used to resolve to whichever block came
    last in GROUPS, which hid nine wrong answers: Azores, Cyprus and Chita were
    all overwritten into the wrong continent, Galapagos into North America, and
    "Leeward Is"/"Windward Is" out of the Caribbean and into Australia. Nothing
    reported it -- the table just quietly asserted the wrong thing, and the
    continents reached the tree. So a conflict is now a hard error, and the fix
    is to say which block was right.
    """
    table = {}
    home: dict[str, str] = {}
    conflicts = []
    for continent, block in GROUPS.items():
        for name in _lines(block):
            if name in home and home[name] != continent:
                conflicts.append(f"{name!r}: {home[name]} and {continent}")
                continue
            home.setdefault(name, continent)
            table[name] = [continent]
    if conflicts:
        raise AssertionError(
            "Locality listed under two continents -- keep it in one block:\n  "
            + "\n  ".join(sorted(conflicts)))
    for name, value in MULTI.items():
        table[name] = list(value)
    return table


LOCALITY_TO_CONTINENT = _build()
_BY_FOLD = {}
for _k, _v in LOCALITY_TO_CONTINENT.items():
    _BY_FOLD.setdefault(_fold(_k), _v)


def continent_for(locality: str):
    """Continent list for an OSF locality, or None when deliberately unmapped."""
    v = LOCALITY_TO_CONTINENT.get((locality or "").strip()) or _BY_FOLD.get(_fold(locality))
    if v and all(x in VALID for x in v):
        return sorted(set(v))
    return None


# A sub-national qualifier, a multi-country range and a comma inside a qualifier
# all occur in checklists that record distribution as one free-text string, and
# this is the shape of all three:
#
#   "Australia (Queensland)"                  one place, one country
#   "Canada, USA"                             two countries, two continents
#   "Australia (Queensland, New South Wales)" one place -- and splitting it on
#                                            the inner comma invents a second
#
# So the parenthetical is removed FIRST and only then is the string split. Doing
# it the other way round is how "Australia (Queensland, New South Wales)"
# becomes "Queensland", which is not a place this table has ever heard of, and
# the whole record falls out as unmapped.
_PAREN = re.compile(r"\s*\([^)]*\)")


def area_parts(area: str):
    """The individual places a free-text distribution string names, in order."""
    stripped = _PAREN.sub("", area or "")
    return [p.strip() for p in stripped.split(",") if p.strip()]


def continent_for_area(area: str):
    """Continents for one distribution string, or None if any part is unmapped.

    The all-or-nothing return is the point. A record like "Canada, USA, and an
    island this table has never heard of" must not resolve to North America:
    that records a range narrower than the source states, and a species with a
    missing continent is the state it was already in, whereas a species with a
    wrong one is a new error.
    """
    whole = continent_for(area)
    if whole:
        return whole
    parts = area_parts(area)
    if not parts:
        return None
    out = set()
    for part in parts:
        c = continent_for(part)
        if not c:
            return None
        out.update(c)
    return sorted(out)


if __name__ == "__main__":
    import sys
    names = [ln.strip() for ln in open(sys.argv[1], encoding="utf-8") if ln.strip()]
    missing = [n for n in names
               if not (LOCALITY_TO_CONTINENT.get(n) or _BY_FOLD.get(_fold(n)))]
    print(f"localities: {len(names):,}")
    print(f"  mapped:   {len(names) - len(missing):,} "
          f"({(len(names) - len(missing))/max(len(names), 1)*100:.1f}%)")
    print(f"  UNMAPPED: {len(missing)}")
    for n in missing:
        tag = "(deliberate)" if n in UNMAPPED_NOTE else "*** UNEXPECTED ***"
        print(f"     {n}  {tag}")
