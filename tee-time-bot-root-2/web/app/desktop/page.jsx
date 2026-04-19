import ScreenDesktop from "@/components/screen-desktop";
import { getDashboardData } from "@/lib/backend";

export const dynamic = "force-dynamic";

export default async function Page() {
  const { teeTimes, courses } = await getDashboardData();
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
