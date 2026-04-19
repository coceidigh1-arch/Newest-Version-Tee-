import ScreenDesktop from "@/components/screen-desktop";

export default function Page() {
  return (
    <main className="stage-desktop">
      <div style={{
        boxShadow: "0 40px 80px rgba(0,0,0,0.18), 0 0 0 1px rgba(0,0,0,0.12)",
        borderRadius: 8, overflow: "hidden",
      }}>
        <ScreenDesktop/>
      </div>
    </main>
  );
}
