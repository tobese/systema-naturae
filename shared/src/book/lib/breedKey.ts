// Breeds are identified by common name, and six names are shared by two host
// species: Abyssinian (cat / cavy), Hampshire (sheep / pig), Hereford (cattle /
// pig), Rex (rabbit / cavy), Silkie (chicken / cavy), Texel (sheep / cavy). A
// sidecar keyed on the bare name can only hold one of each pair, which is how
// breed-images.json came to carry a photograph of the wrong animal for half of
// them.
//
// So breed entries in that sidecar - and in the per-chapter `images` map the
// book decorates from - are keyed by host species first: "cat-Persian",
// "cavy-Silkie", "sheep-Hampshire". Species entries stay keyed by binomial, which
// is already unique.
//
// The host species is the only correct discriminator, not the family: caprinae
// holds both sheep and goats, and anatidae both ducks and geese, so no
// per-family animal word can be right. Both the generator that writes these keys
// and the runtime that reads them resolve the host the same way, from the
// species node the breed hangs under.

const HOST_TOKENS: Record<string, string> = {
  Felis: "cat",
  Canis: "dog",
  Equus: "horse",
  Capra: "goat",
  Ovis: "sheep",
  Sus: "pig",
  Bos: "cattle",
  Gallus: "chicken",
  Meleagris: "turkey",
  Anas: "duck",
  Anser: "goose",
  Columba: "pigeon",
  Oryctolagus: "rabbit",
  Cavia: "cavy",
};

// A breed with no resolvable host gets a visibly-wrong key rather than a bare
// one, so the collision resurfaces as a missing portrait instead of silently
// overwriting another species' entry.
const UNKNOWN = "unknown";

export function hostToken(species: string | undefined | null): string {
  const genus = (species ?? "").trim().split(/\s+/)[0];
  return HOST_TOKENS[genus] ?? UNKNOWN;
}

export function breedKey(species: string | undefined | null, name: string): string {
  return `${hostToken(species)}-${name}`;
}
