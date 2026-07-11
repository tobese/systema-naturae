const KINGDOMS: { slug: string; label: string; hue: number }[] = [
  { slug: "animalia", label: "Animals", hue: 45 },
  { slug: "plantae", label: "Plants", hue: 120 },
  { slug: "fungi", label: "Fungi", hue: 25 },
  { slug: "chromista", label: "Chromista", hue: 200 },
  { slug: "protozoa", label: "Protozoa", hue: 280 },
  { slug: "archaea", label: "Archaea", hue: 340 },
];

export default function KingdomSwitcher({ current }: { current: string }) {
  const base = (import.meta as { env?: { BASE_URL?: string } }).env?.BASE_URL ?? "/";
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 4, flexWrap: "wrap" }}>
      {KINGDOMS.map(k => {
        const active = k.slug === current;
        const accent = `hsl(${k.hue}, 55%, 55%)`;
        return (
          <a
            key={k.slug}
            href={active ? undefined : `${base}${k.slug}.html`}
            title={active ? `Current: ${k.label}` : `Switch to ${k.label}`}
            style={{
              fontSize: 11,
              fontWeight: active ? 700 : 500,
              letterSpacing: "0.02em",
              textDecoration: "none",
              padding: "3px 9px",
              borderRadius: 999,
              cursor: active ? "default" : "pointer",
              color: active ? "#0b0d14" : accent,
              background: active ? accent : "transparent",
              border: `1px solid ${active ? accent : "#2a2d40"}`,
              transition: "background 0.12s, color 0.12s, border-color 0.12s",
            }}
          >
            {k.label}
          </a>
        );
      })}
    </div>
  );
}
