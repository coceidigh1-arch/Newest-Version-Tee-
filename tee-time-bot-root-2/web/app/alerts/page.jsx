import { Phone } from "@/components/ios-frame";
import ScreenAlerts from "@/components/screen-alerts";
import { TabBar } from "@/components/screen-dashboard";

export default function Page() {
  return (
    <main className="stage">
      <Phone>
        <ScreenAlerts/>
        <TabBar active="bell"/>
      </Phone>
    </main>
  );
}
