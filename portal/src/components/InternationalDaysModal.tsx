import { useEffect, useMemo } from "react";
import { useInternationalDays, type InternationalDay } from "../hooks/useInternationalDays";

function formatMonthDay(monthDay: string): string {
  const [mm, dd] = monthDay.split("-").map(Number);
  return new Date(2000, mm - 1, dd).toLocaleDateString("en-US", { month: "long", day: "numeric" });
}

function getMonthName(monthDay: string): string {
  const [mm] = monthDay.split("-").map(Number);
  return new Date(2000, mm - 1, 1).toLocaleDateString("en-US", { month: "long" });
}

function WikipediaIcon() {
  return (
    <svg width={12} height={12} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" style={{ flexShrink: 0 }}>
      <circle cx="12" cy="12" r="10" />
      <line x1="2" y1="12" x2="22" y2="12" />
      <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z" />
    </svg>
  );
}

function ExternalIcon() {
  return (
    <svg width={11} height={11} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" style={{ flexShrink: 0 }}>
      <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6" />
      <polyline points="15 3 21 3 21 9" />
      <line x1="10" y1="14" x2="21" y2="3" />
    </svg>
  );
}

function DayEntry({ day, highlight, onNavigate }: { day: InternationalDay; highlight?: boolean; onNavigate?: (slug: string) => void }) {
  return (
    <div style={{
      padding: "14px 0",
      borderBottom: "1px solid #181824",
      background: highlight ? "rgba(80, 120, 80, 0.08)" : "transparent",
      borderRadius: highlight ? 6 : 0,
      paddingLeft: highlight ? 12 : 0,
      paddingRight: highlight ? 12 : 0,
      marginLeft: highlight ? -12 : 0,
      marginRight: highlight ? -12 : 0,
    }}>
      <div style={{ display: "flex", alignItems: "baseline", gap: 10, marginBottom: 5 }}>
        <span style={{ fontSize: 14, fontWeight: 600, color: highlight ? "#a8d8a8" : "#d0d0e8" }}>
          {day.title}
        </span>
        <span style={{ fontSize: 11, color: "#444", flexShrink: 0 }}>
          {formatMonthDay(day.monthDay)}
        </span>
      </div>
      <p style={{ margin: "0 0 8px", fontSize: 12.5, color: "#888", lineHeight: 1.55 }}>
        {day.description}
      </p>
      <div style={{ display: "flex", gap: 14, alignItems: "center", flexWrap: "wrap" }}>
        <a
          href={day.wikipediaUrl}
          target="_blank"
          rel="noopener noreferrer"
          style={{ display: "flex", alignItems: "center", gap: 4, fontSize: 11, color: "#9aaacc", textDecoration: "none" }}
          onMouseEnter={e => { e.currentTarget.style.color = "#b8c8e8"; }}
          onMouseLeave={e => { e.currentTarget.style.color = "#9aaacc"; }}
        >
          <WikipediaIcon />
          Wikipedia
        </a>
        {day.officialUrl && (
          <a
            href={day.officialUrl}
            target="_blank"
            rel="noopener noreferrer"
            style={{ display: "flex", alignItems: "center", gap: 4, fontSize: 11, color: "#9aaacc", textDecoration: "none" }}
            onMouseEnter={e => { e.currentTarget.style.color = "#b8c8e8"; }}
            onMouseLeave={e => { e.currentTarget.style.color = "#9aaacc"; }}
          >
            <ExternalIcon />
            Official site
          </a>
        )}
        {onNavigate && day.relatedFamilies?.map(fam => (
          <button
            key={fam.slug}
            onClick={() => onNavigate(fam.slug)}
            style={{ display: "flex", alignItems: "center", gap: 4, background: "none", border: "none", padding: 0, cursor: "pointer", fontSize: 11, color: "#7aaa7a" }}
            onMouseEnter={e => { e.currentTarget.style.color = "#9acc9a"; }}
            onMouseLeave={e => { e.currentTarget.style.color = "#7aaa7a"; }}
          >
            <svg width={11} height={11} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2.2} strokeLinecap="round" strokeLinejoin="round">
              <path d="M5 12h14M12 5l7 7-7 7" />
            </svg>
            {fam.label} in portal
          </button>
        ))}
      </div>
    </div>
  );
}

interface Props {
  onClose: () => void;
  onNavigate: (slug: string) => void;
}

export default function InternationalDaysModal({ onClose, onNavigate }: Props) {
  const { days, todaysDays } = useInternationalDays();

  useEffect(() => {
    const handler = (e: KeyboardEvent) => { if (e.key === "Escape") { e.stopPropagation(); onClose(); } };
    document.addEventListener("keydown", handler);
    return () => document.removeEventListener("keydown", handler);
  }, [onClose]);

  const byMonth = useMemo(() => {
    const map = new Map<string, InternationalDay[]>();
    for (const day of days) {
      const month = getMonthName(day.monthDay);
      if (!map.has(month)) map.set(month, []);
      map.get(month)!.push(day);
    }
    return map;
  }, [days]);

  const todayIds = new Set(todaysDays.map(d => d.id));
  const currentMonth = getMonthName(
    `${String(new Date().getMonth() + 1).padStart(2, "0")}-01`,
  );

  return (
    <div
      onClick={onClose}
      style={{
        position: "fixed",
        inset: 0,
        background: "rgba(0,0,0,0.72)",
        zIndex: 200,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        padding: 24,
      }}
    >
      <div
        onClick={e => e.stopPropagation()}
        style={{
          position: "relative",
          background: "#0f1117",
          border: "1px solid #1e2030",
          borderRadius: 10,
          width: "100%",
          maxWidth: 620,
          maxHeight: "82vh",
          overflowY: "auto",
          boxShadow: "0 16px 48px rgba(0,0,0,0.7)",
        }}
      >
        <button
          onClick={onClose}
          style={{
            position: "absolute",
            top: 12,
            right: 14,
            background: "transparent",
            border: "none",
            color: "#555",
            fontSize: 20,
            cursor: "pointer",
            lineHeight: 1,
            padding: "2px 6px",
          }}
          onMouseEnter={e => { e.currentTarget.style.color = "#aaa"; }}
          onMouseLeave={e => { e.currentTarget.style.color = "#555"; }}
        >
          ×
        </button>

        <div style={{ padding: "24px 28px 28px" }}>
          <div style={{ marginBottom: 20 }}>
            <h2 style={{ margin: "0 0 4px", fontSize: 17, fontWeight: 600, color: "#d8d8e8", letterSpacing: "-0.01em" }}>
              International Nature Days
            </h2>
            <p style={{ margin: 0, fontSize: 12, color: "#444" }}>
              Annual observances celebrating wildlife, conservation, and the natural world
            </p>
          </div>

          {todaysDays.length > 0 && (
            <div style={{
              background: "rgba(60, 100, 60, 0.12)",
              border: "1px solid rgba(80, 140, 80, 0.25)",
              borderRadius: 8,
              padding: "12px 16px",
              marginBottom: 24,
            }}>
              <div style={{ fontSize: 11, fontWeight: 600, letterSpacing: "0.06em", textTransform: "uppercase", color: "#80b880", marginBottom: 10 }}>
                Today — {formatMonthDay(todaysDays[0].monthDay)}
              </div>
              {todaysDays.map(day => (
                <DayEntry key={day.id} day={day} highlight onNavigate={onNavigate} />
              ))}
            </div>
          )}

          {Array.from(byMonth.entries()).map(([month, monthDays]) => (
            <div key={month} style={{ marginBottom: 8 }}>
              <div style={{
                fontSize: 11,
                fontWeight: 600,
                letterSpacing: "0.06em",
                textTransform: "uppercase",
                color: month === currentMonth ? "#7a9a7a" : "#3a3d50",
                padding: "8px 0 4px",
                marginBottom: 2,
                borderBottom: "1px solid #181824",
              }}>
                {month}
              </div>
              {monthDays.map(day => (
                <DayEntry key={day.id} day={day} highlight={todayIds.has(day.id)} onNavigate={onNavigate} />
              ))}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
