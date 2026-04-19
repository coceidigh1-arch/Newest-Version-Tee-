import { Phone } from "@/components/ios-frame";
import ScreenDashboard from "@/components/screen-dashboard";
import { getDashboardData } from "@/lib/backend";

export const dynamic = "force-dynamic";

export default async function Page() {
  const { teeTimes, courses, isSample } = await getDashboardData();
  return (
    <main className="stage">
      <Phone>
        <ScreenDashboard
          teeTimes={teeTimes}
          courses={courses}
          isSample={isSample}
          totalCount={teeTimes.length}
        />
      </Phone>
    </main>
  );
}
