import { Phone } from "@/components/ios-frame";
import ScreenAlerts from "@/components/screen-alerts";
import { TabBar } from "@/components/screen-dashboard";
import { getDashboardData } from "@/lib/backend";

export const dynamic = "force-dynamic";

export default async function Page() {
  const { alerts } = await getDashboardData();
  return (
    <main className="stage">
      <Phone>
        <ScreenAlerts alerts={alerts}/>
        <TabBar active="bell"/>
      </Phone>
    </main>
  );
}
