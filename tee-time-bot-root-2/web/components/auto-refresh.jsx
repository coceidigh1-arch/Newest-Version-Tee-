"use client";
import React from "react";
import { useRouter } from "next/navigation";

// Invalidates the RSC payload every `intervalMs` so the server component
// re-fetches /slots + /courses. Respects page visibility (pauses when the
// tab is hidden) to avoid hammering the backend.
export default function AutoRefresh({ intervalMs = 60000 }) {
  const router = useRouter();
  React.useEffect(() => {
    let t;
    function tick() {
      if (document.visibilityState === "visible") router.refresh();
      t = setTimeout(tick, intervalMs);
    }
    t = setTimeout(tick, intervalMs);
    return () => clearTimeout(t);
  }, [router, intervalMs]);
  return null;
}
