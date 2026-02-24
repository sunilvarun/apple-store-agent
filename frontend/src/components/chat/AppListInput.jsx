import { useState } from "react";
import { Sparkles } from "lucide-react";

export default function AppListInput({ onSubmit }) {
  const [apps, setApps] = useState("");

  const handleSubmit = () => {
    const list = apps.split(/[\n,]+/).map(a => a.trim()).filter(Boolean);
    if (!list.length) return;
    onSubmit("What iPhone should I get?", list);
  };

  const appCount = apps.split(/[\n,]+/).map(a => a.trim()).filter(Boolean).length;

  return (
    <div className="p-4 border-b border-gray-100">
      <p className="text-xs font-medium text-apple-dark mb-2">Paste your apps for a personalised recommendation</p>
      <textarea
        value={apps}
        onChange={e => setApps(e.target.value)}
        placeholder={"Lightroom\nCapCut\nGenshin Impact\nZoom\n..."}
        rows={4}
        className="w-full text-sm px-3 py-2 rounded-xl resize-none outline-none"
        style={{ background: "#F5F5F7", border: "1px solid #E5E5EA", color: "#1D1D1F" }}
      />
      <div className="flex items-center justify-between mt-2">
        <span className="text-xs text-apple-light">{appCount > 0 ? `${appCount} app${appCount > 1 ? "s" : ""} detected` : ""}</span>
        <button
          onClick={handleSubmit}
          disabled={!appCount}
          className="flex items-center gap-1.5 px-4 py-1.5 rounded-full text-xs font-medium text-white transition-opacity disabled:opacity-40"
          style={{ background: "#0071E3" }}>
          <Sparkles size={12} />
          Get Recommendation
        </button>
      </div>
    </div>
  );
}
