import { Phone } from "@/components/ios-frame";
import ScreenDetail from "@/components/screen-detail";
import { getDashboardData } from "@/lib/backend";

export const dynamic = "force-dynamic";

export default async function Page({ params }) {
  const { id } = await params;
  const { teeTimes, courses } = await getDashboardData({ limit: 300 });
  const tt = teeTimes.find(t => t.id === id) || teeTimes[0];
  return (
    <main className="stage">
      <Phone>
        <ScreenDetail teeTime={tt} courses={courses}/>
      </Phone>
    </main>
  );
}
