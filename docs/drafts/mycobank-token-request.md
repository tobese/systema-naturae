# Draft: MycoBank web-service access token request

**Status: draft, not sent.**

**There is no email address to send this to.** Checked 2026-10-01:

| where | result |
|---|---|
| `mycobank.org/Contact` | web form (Name/Email/Subject/Message + reCAPTCHA), no address in the DOM |
| `mycobank.org/FAQ_and_help` | no address |
| `bio-aware.com/contact` | no address |
| footer on every page | curators by postal address only (Dr. K. Bensch, Westerdijk Fungal Biodiversity Institute, Utrecht) |
| DNS `MX mycobank.org` | `mycobank-org.mail.protection.outlook.com` — a gateway, not a mailbox |
| re3data.org entry for MycoBank | lists `https://www.mycobank.org/Contact` as the administrative contact |

**So this has to go through the contact form**, and the `Email` field is there for *our* address, not theirs. Paste the body below at `https://www.mycobank.org/Contact`.

The old draft suggested `bio-aware.com` as an alternative route. Worth knowing that bio-aware is not an independent third party here — it is the platform vendor, and its BioloMICS software *is* the MycoBank website ("Website built using BioloMICS Software", footer). Asking them is asking the operator, not a fallback.

## What changed since the previous draft

**Ask #2 (a bulk route) is answered — delete it.** The previous version asked whether a dump or export path existed. It does, is linked from the homepage, needs no key and no registration:

```
https://www.mycobank.org/Images/MBList.zip     # 144 MB, MBList.xlsx, 544,942 rows
```

Parsed 2026-10-01: **521,820 unique taxon names**, of which 426,834 are rank `sp.`, plus 21,201 genera, 55,905 varieties, 24,571 forms, 3,270 families. Columns: ID, Taxon name, Synonymy, Authors, Authors (abbreviated), Year of effective publication, Name status, MycoBank #, Classification, Rank.

Coverage against our own undescribed species:

| | |
|---|---|
| undescribed fungal species in our tree | 157,690 |
| found in MBList.xlsx | **153,443 (97.3%)** |
| not found | 4,247 (2.7%) |

This supersedes the EOL/Zenodo `MycoBank: MycoBank (671) DwCA` route found on 2026-09-30, which matched 132,962 of 157,669 (84.3%). The Excel export is larger, more current (export date 7 January 2026), needs no Zenodo round-trip, and carries a `Name status` column (`Legitimate` / `Illegitimate` / `Orthographic variant` / `Invalid` / `Unavailable`) plus a rendered `Classification` path.

The 4,247 misses are real absences, not authority-suffix artefacts. Spot-checked: `Polyphlyctis cystofera`, `Septosperma anomalum` and `Karlingiomyces laevis` are stored in our tree with **no** author string at all, so there is nothing to strip and nothing to retry.

**Still nomenclature only.** There is no prose in it, so it does not close the description gap. Which leaves exactly the one question worth asking a human.

**The licence is CC BY-NC, not CC-BY 4.0.** The footer on every page links `https://creativecommons.org/licenses/by-nc/4.0/`, and some pages carry CC BY-NC-ND. The previous draft asserted "MycoBank data is CC-BY 4.0" — that is wrong, and asking for a token while misstating the licence would be a poor start. Non-commercial use with attribution is fine for this project; ND would forbid adaptation, so it is worth asking which applies to the descriptive fields.

---

## Subject

Web service access token — non-commercial taxonomic enrichment project

## Body

Dear MycoBank team,

I maintain Systema Naturae, a free open-source taxonomy portal
(https://github.com/tobese/systema-naturae) presenting six kingdoms of life
from an integrated taxonomic tree. Fungal coverage is the weak point: we hold
about 3,900 described fungal species out of 161,716 in our tree, or 2.4%, and
essentially all of it came from English Wikipedia — the worst available source
for fungal nomenclature, since en.wikipedia has articles for a few thousand of
roughly 145,000 named fungi.

I have already found and used the `MBList.xlsx` export linked from your
homepage, which is exactly what I needed for nomenclature — thank you for
making that available without registration. Against our undescribed species it
matches 153,443 of 157,690 (97.3%), and the `Name status` and `Classification`
columns answer synonymy questions I would otherwise have to guess at.

What it does not carry is prose. So my one request is an access token for
whatever interface exposes the descriptive fields. The documentation I have
found describes two, and I cannot tell which is current:

- A legacy SOAP/REST search service at
  `http://www.mycobank.org/Services/Generic/SearchService.svc/rest/xml`, whose
  response fields included a `Summary` value (field `E3787`) and a `Synonymy`
  value (field `E4060`). The help page I have a note of,
  `.../Services/Generic/Help.aspx?s=searchservice`, now 404s.
- A JSON endpoint at
  `https://webservices.bio-aware.com/cbsdatabase_new/mycobank/taxonnames`,
  which requires an `Authorization: Bearer` token, with
  `MYCOBANK_ACCESS_TOKEN` in every example I can find.

Which of these is the supported interface, and could I have a token for it? If
the legacy endpoint still works without a token that would be simpler, but I
would rather use the supported one.

Two smaller things, if they are quick to answer:

1. **Which licence governs the descriptive fields specifically?** The site
   footer says CC BY-NC, and I have seen CC BY-NC-ND on some pages. I want to
   be sure before storing text and displaying it in a tree view.
2. **Is a bulk route to descriptive fields possible at all?** At ~150,000
   species even a few requests per second is a long run. If descriptions exist
   only per-record through the API, that is a real constraint and I would
   rather scope the project to it than discover it later.

If descriptive fields turn out not to be available through any API, that is a
genuinely useful answer and I will build against MycoBank and Index Fungorum
for nomenclature only, and accept that fungal prose has to come from literature
treatments.

The project is non-commercial and open source. I can cache aggressively to
disk, work at a modest rate with backoff, and resume across runs. I would also
credit MycoBank explicitly and keep a link to each record's MycoBank identifier,
so attribution is straightforward if the licence requires it.

Thank you for your time, and for maintaining the resource.

Best regards,

Tommy Bergstrand
tommy.bergstrand@gmail.com
https://github.com/tobese/systema-naturae

---

## Notes to self before sending

- **Not an email.** Goes in the contact form at `https://www.mycobank.org/Contact`.
  The `Email` field is for our address. Expect reCAPTCHA — that part is manual.
- Already trimmed per the decision to cut to the essentials: the attribution
  and rate-limiting commitments are gone, replaced by a single short paragraph
  that offers them rather than promises them. The `sourcedFrom: "mycobank"`
  detail and the CC-BY claim both came out — the licence question is now asked
  rather than asserted.
- **Do not claim CC-BY 4.0.** It is CC BY-NC per the footer. Ask instead.
- The previous draft's fallback note said the GBIF/Plazi route was "measured at
  8% on fungi". **Wrong by ~20x** — the real measured yield is **0.37%**
  (151 of 40,278 agaricomycetes binomials). The 8% came from a 20-species
  probe and should never have been trusted. At 0.37%, GBIF descriptions for
  fungi are effectively absent: GBIF matches the names at confidence 99 and
  simply holds no prose, because its description store is built from Plazi
  literature treatments and there is very little for fungi. So the honest
  fallback is literature treatments, not GBIF.
- AlgaeBase (€500–1000/yr) is a separate, paid conversation. Do not merge it
  into this one. AlgaeBase is nominally already inside COL's 3LR dataset, but
  COL exposed no descriptive content either.
- EOL's publishing/traits API needs an admin-issued JWT ("contact hammockj AT
  si.edu"), returns structured traits rather than prose, and has no field in
  our schema. Not this letter.