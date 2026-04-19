import { Phone } from "@/components/ios-frame";
import ScreenCourses from "@/components/screen-courses";
import { TabBar } from "@/components/screen-dashboard";

export default function Page() {
  return (
    <main className="stage">
      <Phone>
        <ScreenCourses/>
        <TabBar active="map"/>
      </Phone>
    </main>
  );
}
