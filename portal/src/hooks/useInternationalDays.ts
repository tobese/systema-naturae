import { useMemo } from "react";
import rawDays from "../../data/international-days.json";

export interface InternationalDay {
  id: string;
  monthDay: string;
  title: string;
  description: string;
  wikipediaUrl: string;
  officialUrl?: string;
}

export function useInternationalDays() {
  const days = useMemo(
    () => (rawDays as { updatedAt: string; days: InternationalDay[] }).days,
    [],
  );

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
