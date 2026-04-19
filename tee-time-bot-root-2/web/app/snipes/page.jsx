import { Phone } from "@/components/ios-frame";
import ScreenSnipe from "@/components/screen-snipe";
import { TabBar } from "@/components/screen-dashboard";

export const dynamic = "force-dynamic";

// Snipes are per-user (keyed by telegram_chat_id). Without a session context
// the Fairway app can only render an empty state pointing to the Telegram bot.
// When the product grows a user login, pass the user's snipes as props here.
export default function Page() {
  return (
    <main className="stage">
      <Phone>
        <ScreenSnipe snipes={[]}/>
        <TabBar active="snipe"/>
      </Phone>
    </main>
  );
}
