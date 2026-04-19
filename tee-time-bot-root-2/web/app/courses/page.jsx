import { Phone } from "@/components/ios-frame";
import ScreenCourses from "@/components/screen-courses";
import { TabBar } from "@/components/screen-dashboard";
import { getCourses } from "@/lib/backend";

export const dynamic = "force-dynamic";

export default async function Page() {
  const courses = await getCourses();
  return (
    <main className="stage">
      <Phone>
        <ScreenCourses courses={courses}/>
        <TabBar active="map"/>
      </Phone>
    </main>
  );
}
