import { Phone } from "@/components/ios-frame";
import ScreenDashboard from "@/components/screen-dashboard";
import AutoRefresh from "@/components/auto-refresh";
import { getDashboardData } from "@/lib/backend";
import { filtersFromSearchParams } from "@/lib/filters";

export const dynamic = "force-dynamic";

export default async function Page({ searchParams }) {
  const sp = await searchParams;
  const filters = filtersFromSearchParams(sp);
  const { teeTimes, courses, isSample, totalMatches } = await getDashboardData({
    filters,
    limit: 12,
  });
  return (
    <main className="stage">
      <AutoRefresh intervalMs={60000}/>
      <Phone>
        <ScreenDashboard
          teeTimes={teeTimes}
          courses={courses}
          isSample={isSample}
          totalCount={totalMatches ?? teeTimes.length}
          activeFilters={filters}
        />
      </Phone>
    </main>
  );
}
