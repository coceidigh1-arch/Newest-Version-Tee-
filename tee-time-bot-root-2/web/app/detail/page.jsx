import { Phone } from "@/components/ios-frame";
import ScreenDetail from "@/components/screen-detail";
import { getDashboardData } from "@/lib/backend";

export const dynamic = "force-dynamic";

export default async function Page() {
  const { teeTimes, courses } = await getDashboardData();
  return (
    <main className="stage">
      <Phone>
        <ScreenDetail teeTimes={teeTimes} courses={courses}/>
      </Phone>
    </main>
  );
}
