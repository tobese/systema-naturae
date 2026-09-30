# Draft: MycoBank web-service access token request

**Status: draft, not sent.** Addresses below are taken from the MycoBank web
service and API documentation. Re-check the recipient before sending — the
`bio-aware.com` host is a third-party service operator, not MycoBank itself, so
it is worth asking MycoBank which channel they consider current rather than
assuming the one in the docs.

**Suggested recipients**

- `pier.kuipers@algaebase.org` — AlgaeBase only, if the algae side is ever
  wanted. AlgaeBase is a paid API (€500–1000/yr), so this is a purchase
  conversation, not a key request. Not the right recipient for fungi.
- For MycoBank, the documented route is the web-services help page
  (`http://www.mycobank.org/Services/Generic/Help.aspx?s=searchservice`).
  MycoBank's own contact form is the safer address than a scraped one.

---

## Subject

Web service access for a non-commercial taxonomic enrichment project

## Body

Dear MycoBank team,

I am working on Systema Naturae, a free open-source taxonomy portal
(https://github.com/tobese/systema-naturae) that presents six kingdoms of life
from an integrated taxonomic tree. We currently hold roughly 3,900 described
fungal species out of 161,716 in our tree — fungal coverage is 2.4%, essentially
all of it from English Wikipedia, which is far and away the worst available
source for fungal nomenclature.

I would like to use MycoBank as a nomenclatural and descriptive source to close
that gap. I have two specific asks:

**1. An access token for the web service.** The public documentation I have
found describes two different endpoints:

- A legacy SOAP/REST search service at
  `http://www.mycobank.org/Services/Generic/SearchService.svc/rest/xml`, whose
  response fields included a `Summary` value (field `E3787`) and a `Synonymy`
  value (field `E4060`). This appears to be the older interface.
- A newer JSON endpoint at
  `https://webservices.bio-aware.com/cbsdatabase_new/mycobank/taxonnames`, which
  requires an `Authorization: Bearer` token, with an
  `MYCOBANK_ACCESS_TOKEN` environment variable in every example I can find.

Which of these is the currently supported interface, and could I have a token
for it? If the legacy SOAP endpoint is still functional without a token, that
would be simpler, but I would rather use the supported one.

**2. A bulk route, if one exists.** Our target is on the order of 150,000 fungal
species names, so per-species requests will be slow even with a token. Is there
a dump or export path — a Darwin Core Archive, a periodically regenerated file,
or a bulk endpoint — that you would recommend for this volume? Index Fungorum's
`NamesByCurrentKey` service is documented and I can use that for nomenclature,
but I do not see an equivalent bulk route for MycoBank's descriptive fields.

A little about how the data would be used, in case it matters for your
conditions:

- Non-commercial, no revenue, no resale. The portal is free and open source.
- Every fetched description would be stored with `sourcedFrom: "mycobank"` so
  its origin is explicit and visible in the UI, and every species record keeps a
  link back to its MycoBank identifier.
- Attribution: MycoBank data is CC-BY 4.0, and the portal credits its sources.
- The work is reproducible: the fetch script and the accepted/rejected decision
  log would both be committed to the repository.
- Rate limiting is not a problem I want to impose. I can work at a few requests
  per second with backoff, cache aggressively to disk, and resume across runs.

If descriptive fields are not available through the API at all, that is a
perfectly useful answer and I will build against Index Fungorum for nomenclature
and accept that fungal descriptions have to come from literature treatments
instead. I would rather know the real constraint than guess at it.

Thank you for your time, and for maintaining the resource.

Best regards,

[your name]
[your email]
https://github.com/tobese/systema-naturae

---

## Notes to self before sending

- Do not send this without reading it. It commits to attribution behaviour and a
  rate limit on the project's behalf.
- If the answer is that MycoBank has no API access to `Summary`, the fallback is
  the GBIF/Plazi route already measured at 8% on fungi, and the honest
  conclusion becomes: fungal descriptions are not cheaply available, and the
  2.4% figure is close to what the free web is worth.
- AlgaeBase is a separate, paid conversation. Don't merge them.
