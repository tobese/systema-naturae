package main

import (
	"bytes"
	"encoding/json"
	"fmt"
)

// onode is a JSON object that preserves key order through decode -> mutate
// -> encode. A plain map[string]any loses order on decode (Go map iteration
// is randomized) and encoding/json re-sorts map keys alphabetically on
// encode — fine for a program that only reads its own output, but these
// files are reviewed as git diffs, and a no-op merge that re-sorts every
// key turns into a 100%-of-lines diff with zero semantic change. Found by
// running the real importer against real data (see README's "Known issue
// found by that test").
type onode struct {
	keys []string
	vals map[string]any // string, float64, bool, nil, *onode, or []any
}

func newONode() *onode {
	return &onode{vals: map[string]any{}}
}

// nodeFrom builds an onode from a plain map, for callers (tests, mostly)
// that don't care about key order.
func nodeFrom(fields map[string]any) *onode {
	n := newONode()
	for k, v := range fields {
		n.set(k, v)
	}
	return n
}

func (n *onode) get(key string) any {
	if n == nil {
		return nil
	}
	return n.vals[key]
}

func (n *onode) str(key string) string {
	if v, ok := n.get(key).(string); ok {
		return v
	}
	return ""
}

// set assigns key's value, preserving its existing position if already
// present and appending it (last) otherwise. This is the only way keys
// are added, so insertion order is always exactly what the code did.
func (n *onode) set(key string, val any) {
	if _, exists := n.vals[key]; !exists {
		n.keys = append(n.keys, key)
	}
	n.vals[key] = val
}

func (n *onode) children() []*onode {
	raw, _ := n.get("children").([]any)
	out := make([]*onode, 0, len(raw))
	for _, c := range raw {
		if o, ok := c.(*onode); ok {
			out = append(out, o)
		}
	}
	return out
}

func (n *onode) setChildren(cs []*onode) {
	arr := make([]any, len(cs))
	for i, c := range cs {
		arr[i] = c
	}
	n.set("children", arr)
}

// mergeObjectField merges two object-valued fields (e.g. sourceIds) key by
// key, existing's keys first in their original order, then any new keys
// incoming introduces, in incoming's order. Returns nil if there is
// nothing to merge (incoming isn't an object).
func mergeObjectField(existing, incoming any) any {
	incomingObj, ok := incoming.(*onode)
	if !ok {
		return nil
	}
	existingObj, ok := existing.(*onode)
	if !ok {
		return incomingObj
	}
	merged := newONode()
	for _, k := range existingObj.keys {
		merged.set(k, existingObj.vals[k])
	}
	for _, k := range incomingObj.keys {
		merged.set(k, incomingObj.vals[k])
	}
	return merged
}

// --- JSON decode: a hand-rolled token walk, because the only way to learn
// a JSON object's original key order is to read it in the order it arrives.

func (n *onode) UnmarshalJSON(data []byte) error {
	dec := json.NewDecoder(bytes.NewReader(data))
	tok, err := dec.Token()
	if err != nil {
		return err
	}
	delim, ok := tok.(json.Delim)
	if !ok || delim != '{' {
		return fmt.Errorf("onode: expected a JSON object, got %v", tok)
	}
	obj, err := decodeObjectBody(dec)
	if err != nil {
		return err
	}
	n.keys, n.vals = obj.keys, obj.vals
	return nil
}

// decodeObjectBody reads key/value pairs until the matching '}', which it
// also consumes. Assumes the opening '{' has already been consumed.
func decodeObjectBody(dec *json.Decoder) (*onode, error) {
	obj := newONode()
	for dec.More() {
		keyTok, err := dec.Token()
		if err != nil {
			return nil, err
		}
		key, ok := keyTok.(string)
		if !ok {
			return nil, fmt.Errorf("onode: expected a string key, got %v", keyTok)
		}
		val, err := decodeValue(dec)
		if err != nil {
			return nil, err
		}
		obj.set(key, val)
	}
	if _, err := dec.Token(); err != nil { // consume '}'
		return nil, err
	}
	return obj, nil
}

// decodeArrayBody mirrors decodeObjectBody for '[' ... ']'.
func decodeArrayBody(dec *json.Decoder) ([]any, error) {
	arr := []any{}
	for dec.More() {
		val, err := decodeValue(dec)
		if err != nil {
			return nil, err
		}
		arr = append(arr, val)
	}
	if _, err := dec.Token(); err != nil { // consume ']'
		return nil, err
	}
	return arr, nil
}

func decodeValue(dec *json.Decoder) (any, error) {
	tok, err := dec.Token()
	if err != nil {
		return nil, err
	}
	if delim, ok := tok.(json.Delim); ok {
		switch delim {
		case '{':
			return decodeObjectBody(dec)
		case '[':
			return decodeArrayBody(dec)
		}
	}
	return tok, nil // string, float64, bool, or nil
}

// --- JSON encode: write keys back out in exactly the recorded order.
// json.MarshalIndent re-indents whatever MarshalJSON returns without
// touching key order, so this is also what produces the pretty-printed
// file on disk.

func (n *onode) MarshalJSON() ([]byte, error) {
	var buf bytes.Buffer
	buf.WriteByte('{')
	for i, k := range n.keys {
		if i > 0 {
			buf.WriteByte(',')
		}
		kb, err := marshalNoEscape(k)
		if err != nil {
			return nil, err
		}
		buf.Write(kb)
		buf.WriteByte(':')
		vb, err := marshalNoEscape(n.vals[k])
		if err != nil {
			return nil, err
		}
		buf.Write(vb)
	}
	buf.WriteByte('}')
	return buf.Bytes(), nil
}

// marshalNoEscape is json.Marshal without HTML-escaping (`&`, `<`, `>` to
// & etc). Needed because this method calls it directly rather than
// going through the reflection-based encoder that a surrounding
// json.Encoder's SetEscapeHTML would otherwise govern — a plain
// json.Marshal call here always escapes, regardless of what flush() does.
// Existing family files have literal "&" (e.g. in authorship strings like
// "Anderson & Handley, 2001"); escaping it on every flush is more diff
// noise for no reason.
func marshalNoEscape(v any) ([]byte, error) {
	var buf bytes.Buffer
	enc := json.NewEncoder(&buf)
	enc.SetEscapeHTML(false)
	if err := enc.Encode(v); err != nil {
		return nil, err
	}
	b := buf.Bytes()
	if n := len(b); n > 0 && b[n-1] == '\n' { // Encode appends one
		b = b[:n-1]
	}
	return b, nil
}

// marshalIndentNoEscape is the non-escaping equivalent of
// json.MarshalIndent, which is hardcoded to escape and offers no way to
// turn it off. Returns bytes already ending in a single newline.
func marshalIndentNoEscape(v any, indent string) ([]byte, error) {
	var buf bytes.Buffer
	enc := json.NewEncoder(&buf)
	enc.SetEscapeHTML(false)
	enc.SetIndent("", indent)
	if err := enc.Encode(v); err != nil {
		return nil, err
	}
	return buf.Bytes(), nil
}
