import { X, BarChart2 } from "lucide-react";

export default function ComparisonBar({ items, onRemove, onCompare }) {
  if (!items.length) return null;

  return (
    <div
      className="fixed bottom-6 left-1/2 -translate-x-1/2 z-40 flex items-center gap-3 px-5 py-3 rounded-2xl shadow-xl"
      style={{ background: "#1D1D1F", minWidth: 320 }}>

      {/* Model thumbnails */}
      <div className="flex items-center gap-2 flex-1">
        {items.map(p => (
          <div key={p.model_slug} className="flex items-center gap-1.5 bg-white/10 px-3 py-1.5 rounded-xl">
            <span className="text-white text-xs font-medium truncate max-w-[80px]">
              {p.display_name.replace("iPhone 17 ", "")}
            </span>
            <button
              onClick={() => onRemove(p)}
              className="text-white/60 hover:text-white transition-colors ml-0.5">
              <X size={11} />
            </button>
          </div>
        ))}

        {/* Placeholder slots */}
        {Array.from({ length: Math.max(0, 2 - items.length) }).map((_, i) => (
          <div key={i} className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl" style={{ border: "1px dashed rgba(255,255,255,0.2)" }}>
            <span className="text-white/30 text-xs">Add model</span>
          </div>
        ))}
      </div>

      {/* Compare button */}
      <button
        onClick={onCompare}
        disabled={items.length < 2}
        className="flex items-center gap-1.5 px-4 py-2 rounded-xl text-sm font-semibold transition-all disabled:opacity-40"
        style={{ background: "#0071E3", color: "#fff" }}>
        <BarChart2 size={13} />
        Compare
      </button>
    </div>
  );
}
