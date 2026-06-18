import { useState, useEffect, useRef } from "react";
import { useSpeciesNews, type NewsEvent } from "../hooks/useSpeciesNews";
import { COLOR_REGISTRY } from "../colorRegistry";

function familyAccent(familySlug: string): string {
  const theme = COLOR_REGISTRY[familySlug];
  if (!theme) return "#556";
  const colors = Object.values(theme.lineageColors);
  return colors[0] ?? "#556";
}

function BellIcon() {
  return (
    <svg width={16} height={16} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.8} strokeLinecap="round" strokeLinejoin="round">
      <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9" />
      <path d="M13.73 21a2 2 0 0 1-3.46 0" />
    </svg>
  );
}

function EventRow({ event }: { event: NewsEvent }) {
  const accent = familyAccent(event.familySlug);
  const isExtinct = event.type === "extinction";
  const isAdded = event.type === "family_added";
  const label = event.commonName || event.name;
  const icon = isExtinct ? "†" : isAdded ? "★" : "✦";
  const iconColor = isExtinct ? "#c06060" : isAdded ? "#9090c8" : "#80b880";

  const inner = (
    <div style={{ display: "flex", gap: 8, alignItems: "flex-start" }}>
      <span style={{ fontSize: 14, color: iconColor, marginTop: 1, flexShrink: 0 }}>
        {icon}
      </span>
      <div style={{ minWidth: 0, flex: 1 }}>
        <div style={{ fontSize: 13, fontWeight: 500, color: "#d8d8d8", marginBottom: 2, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
          {label}
        </div>
        {event.commonName && (
          <div style={{ fontSize: 11, color: "#555", fontStyle: "italic", marginBottom: 4, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
            {event.name}
          </div>
        )}
        <div style={{ display: "flex", gap: 6, alignItems: "center" }}>
          <span style={{ fontSize: 10, color: accent, background: `${accent}22`, padding: "1px 7px", borderRadius: 10, letterSpacing: "0.02em" }}>
            {event.familySlug}
          </span>
          <span style={{ fontSize: 10, color: "#444" }}>{event.date}</span>
          <span style={{ fontSize: 10, color: "#333" }}>{event.source}</span>
        </div>
      </div>
    </div>
  );

  const rowStyle = { display: "block", padding: "10px 14px", borderBottom: "1px solid #1a1a2a", textDecoration: "none", cursor: event.url ? "pointer" : "default" };
  const hoverOn = (e: React.MouseEvent<HTMLElement>) => { e.currentTarget.style.background = "#1a1a2e"; };
  const hoverOff = (e: React.MouseEvent<HTMLElement>) => { e.currentTarget.style.background = "transparent"; };

  if (event.url) {
    return (
      <a href={event.url} target="_blank" rel="noopener noreferrer" style={rowStyle} onMouseEnter={hoverOn} onMouseLeave={hoverOff}>
        {inner}
      </a>
    );
  }
  return (
    <div style={rowStyle} onMouseEnter={hoverOn} onMouseLeave={hoverOff}>
      {inner}
    </div>
  );
}

export default function NewsBell() {
  const { events, unreadCount, markAllSeen } = useSpeciesNews();
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    const handler = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, [open]);

  function toggle() {
    if (!open) markAllSeen();
    setOpen(o => !o);
  }

  return (
    <div ref={ref} style={{ position: "relative" }}>
      <button
        onClick={toggle}
        title={unreadCount > 0 ? `${unreadCount} new species event${unreadCount > 1 ? "s" : ""}` : "Species news"}
        style={{
          position: "relative",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          width: 34,
          height: 34,
          padding: 0,
          borderRadius: 6,
          border: "1px solid",
          borderColor: open ? "#3a3d50" : "#1e2030",
          background: open ? "#1e2030" : "transparent",
          color: unreadCount > 0 ? "#c0c0d8" : "#444",
          cursor: "pointer",
        }}
      >
        <BellIcon />
        {unreadCount > 0 && (
          <span style={{
            position: "absolute",
            top: 5,
            right: 5,
            width: 7,
            height: 7,
            borderRadius: "50%",
            background: "#c05050",
            border: "1.5px solid #0f1117",
          }} />
        )}
      </button>

      {open && (
        <div style={{
          position: "absolute",
          top: "calc(100% + 8px)",
          right: 0,
          width: 320,
          maxHeight: 460,
          overflowY: "auto",
          background: "#141420",
          border: "1px solid #1e2030",
          borderRadius: 8,
          boxShadow: "0 8px 24px rgba(0,0,0,0.6)",
          zIndex: 110,
        }}>
          <div style={{ padding: "9px 14px", borderBottom: "1px solid #1e2030", fontSize: 11, color: "#555", fontWeight: 600, letterSpacing: "0.06em", textTransform: "uppercase" }}>
            Species news
          </div>
          {events.length === 0 ? (
            <div style={{ padding: "24px 14px", fontSize: 13, color: "#444", textAlign: "center" }}>
              No recent events
            </div>
          ) : (
            events.map(e => <EventRow key={e.id} event={e} />)
          )}
        </div>
      )}
    </div>
  );
}
