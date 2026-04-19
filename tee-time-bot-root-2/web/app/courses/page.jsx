import { Phone } from "@/components/ios-frame";
import ScreenCourses from "@/components/screen-courses";
import { TabBar } from "@/components/screen-dashboard";
import { getDashboardData } from "@/lib/backend";

export const dynamic = "force-dynamic";

export default async function Page() {
  const { courses, openSlotsByCourse } = await getDashboardData();
  return (
    <main className="stage">
      <Phone>
        <ScreenCourses courses={courses} openSlotsByCourse={openSlotsByCourse}/>
        <TabBar active="map"/>
      </Phone>
    </main>
  );
}
