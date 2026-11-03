# Data licence

Systema Naturae is a **non-commercial** project.

## The compilation: CC BY 4.0

What this project adds — the selection and arrangement of the tree, its
structure, the merge and placement decisions, the homonym and family-pair
records, the provenance links on every record — is licensed under the
[Creative Commons Attribution 4.0 International licence (CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/).

Attribution: *Systema Naturae (https://github.com/tobese/systema-naturae),
CC BY 4.0*, together with the sources of the parts you use (below).

## The parts: each source's own licence

The data is compiled from published sources. **Every record keeps the
identifiers of the sources it comes from** (`sourceIds` on each species), and
**each source's own licence applies to what comes from it.** The CC BY 4.0
above does not replace those licences; it covers only what this project adds.

The full list — institution, dataset, citation, DOI and licence — is in the
portal under **Sources → Contributors**, filterable by licence, and in
[`data/contributors.json`](data/contributors.json). The licence recorded there
is the one the archive we took states, where it states one.

| licence | what it means for reuse of those parts |
|---|---|
| [CC0](https://creativecommons.org/publicdomain/zero/1.0/) / public domain | no conditions |
| [CC BY](https://creativecommons.org/licenses/by/4.0/) | credit the source |
| [CC BY-SA](https://creativecommons.org/licenses/by-sa/4.0/) | credit, and share adaptations under the same licence (e.g. Wikipedia text) |
| [CC BY-NC](https://creativecommons.org/licenses/by-nc/4.0/) | credit, and **no commercial use** (e.g. MycoBank numbers, iNaturalist common names, Checklist of Vermont Species) |
| [CC BY-NC-SA](https://creativecommons.org/licenses/by-nc-sa/3.0/) | non-commercial and share-alike |
| mixed (GBIF Backbone) | the licence varies per constituent dataset, and which one a record came from is not recorded |

Because the licence follows the record, the tree as a whole has no single
licence: anyone reusing it for a commercial purpose has to leave out the parts
from non-commercial sources, which the provenance on each record makes
possible. Share-alike parts stay separable for the same reason.

Images are not part of the tree. They are shown from Wikimedia Commons and
credited individually, each under its own licence.

How licences are decided per source — including when non-commercial sources
are taken — is in [`docs/licence-issues.md`](docs/licence-issues.md).

## Code

The software in this repository (scripts, services, portal and shared code) is
not covered by this file: it is under the [MIT licence](LICENSE).
