package main

import "strconv"

// importKey identifies a species by one external source's ID, e.g.
// {source: "gbif", id: "2436351"}. This is the contract between importers
// and the merge logic: GBIF, ChecklistBank, ITIS, COL, Wikidata, NCBI,
// WoRMS, TAXREF, BOLD... each importer fills in whichever ID(s) it
// actually resolved on a species' sourceIds field, and any single shared
// (source, id) pair between two submissions is treated as the same
// species — even if the name differs. No new wire format: sourceIds is
// already what TaxonNode carries and every importer already populates it
// in some form; this just uses it for identity instead of only for
// display.
//
// Name match stays as the fallback (see apply() in family.go), for the
// common case where an importer has no cross-reference ID at all yet —
// that was the whole of the identity logic before this.
type importKey struct {
	source string
	id     string
}

func (k importKey) token() string {
	return k.source + ":" + k.id
}

// sourceIDPairs flattens a node's sourceIds field into (source, id) pairs.
// Real data is inconsistent about shape per source — e.g. checklistbank is
// usually a bare string while col/itis/wikidata are usually string arrays
// — and an importer might send a bare JSON number instead of a string, so
// all of those are accepted and normalized to a string id here.
func sourceIDPairs(n *onode) []importKey {
	obj, ok := n.get("sourceIds").(*onode)
	if !ok {
		return nil
	}
	var out []importKey
	for _, source := range obj.keys {
		switch v := obj.vals[source].(type) {
		case string:
			if v != "" {
				out = append(out, importKey{source: source, id: v})
			}
		case float64:
			out = append(out, importKey{source: source, id: formatNumericID(v)})
		case []any:
			for _, item := range v {
				switch s := item.(type) {
				case string:
					if s != "" {
						out = append(out, importKey{source: source, id: s})
					}
				case float64:
					out = append(out, importKey{source: source, id: formatNumericID(s)})
				}
			}
		}
	}
	return out
}

func formatNumericID(f float64) string {
	return strconv.FormatFloat(f, 'f', -1, 64)
}

// matchByID looks up incoming against an index built by sourceIDPairs,
// returning the first existing species that shares any (source, id) pair.
func matchByID(index map[string]*onode, incoming *onode) *onode {
	for _, k := range sourceIDPairs(incoming) {
		if sp, ok := index[k.token()]; ok {
			return sp
		}
	}
	return nil
}

// indexByID records every (source, id) pair a species carries, so a later
// submission can find it by any one of them.
func indexByID(index map[string]*onode, sp *onode) {
	for _, k := range sourceIDPairs(sp) {
		index[k.token()] = sp
	}
}
