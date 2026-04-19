import ScreenDesktop from "@/components/screen-desktop";
import { getDashboardData } from "@/lib/backend";
import { filtersFromSearchParams } from "@/lib/filters";

export const dynamic = "force-dynamic";

export default async function Page({ searchParams }) {
  const sp = await searchParams;
  const filters = filtersFromSearchParams(sp);
  const { teeTimes, courses } = await getDashboardData({ filters, limit: 40 });
  return (
    <main className="stage-desktop">
      <div style={{
        boxShadow: "0 40px 80px rgba(0,0,0,0.18), 0 0 0 1px rgba(0,0,0,0.12)",
        borderRadius: 8, overflow: "hidden",
      }}>
        <ScreenDesktop teeTimes={teeTimes} courses={courses}/>
      </div>
    </main>
  );
}
