import { useState, useMemo, useEffect } from "react";
import baseDays from "../../data/international-days.json";

export interface RelatedFamily {
  slug: string;
  label: string;
}

export interface InternationalDay {
  id: string;
  monthDay: string;
  title: string;
  description: string;
  wikipediaUrl: string;
  officialUrl?: string;
  relatedFamilies?: RelatedFamily[];
}

export function useInternationalDays(kingdom = "animalia") {
  const [kingdomDays, setKingdomDays] = useState<InternationalDay[] | null>(null);

  useEffect(() => {
    if (kingdom === "animalia") {
      setKingdomDays(null);
      return;
    }
    const suffix = `-${kingdom}`;
    fetch(`/data/international-days${suffix}.json`)
      .then(r => (r.ok ? r.json() : null))
      .then((data: any) => {
        if (data && Array.isArray(data.days)) {
          setKingdomDays(data.days as InternationalDay[]);
        } else if (Array.isArray(data)) {
          setKingdomDays(data as InternationalDay[]);
        }
      })
      .catch(() => setKingdomDays(null));
  }, [kingdom]);

  const days = useMemo(() => {
    const base = (baseDays as { updatedAt: string; days: InternationalDay[] }).days;
    if (kingdom === "animalia" || !kingdomDays) return base;
    return kingdomDays;
  }, [kingdom, kingdomDays]);

  const todayMonthDay = useMemo(() => {
    const d = new Date();
    const mm = String(d.getMonth() + 1).padStart(2, "0");
    const dd = String(d.getDate()).padStart(2, "0");
    return `${mm}-${dd}`;
  }, []);

  const todaysDays = useMemo(
    () => days.filter(d => d.monthDay === todayMonthDay),
    [days, todayMonthDay],
  );

  return { days, todaysDays };
}
