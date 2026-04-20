import { Phone } from "@/components/ios-frame";
import ScreenSnipe from "@/components/screen-snipe";
import { TabBar } from "@/components/screen-dashboard";

export const dynamic = "force-dynamic";

export default function Page() {
  return (
    <main className="stage">
      <Phone>
        <ScreenSnipe/>
        <TabBar active="snipe"/>
      </Phone>
    </main>
  );
}
