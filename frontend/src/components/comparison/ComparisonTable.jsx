import { X } from "lucide-react";
import { fmtPrice } from "../../utils/formatters";

// Which specs benefit from higher vs lower values
const SPEC_ROWS = [
  { label: "Price",         key: p => p.starting_price,          fmt: v => fmtPrice(v),           best: "low"  },
  { label: "Chip",          key: p => p.chip,                    fmt: v => v,                     best: null   },
  { label: "Display",       key: p => p.display_size,            fmt: (v, p) => `${v}" ${p.display_type}`, best: "high" },
  { label: "Resolution",    key: p => p.display_resolution,      fmt: v => v,                     best: null   },
  { label: "Rear Cameras",  key: p => p.rear_cameras.length,     fmt: v => `${v}-camera system`,  best: "high" },
  { label: "Optical Zoom",  key: p => parseFloat(p.max_optical_zoom) || 0, fmt: (v, p) => p.max_optical_zoom, best: "high" },
  { label: "Video",         key: p => p.video_max,               fmt: v => v,                     best: null   },
  { label: "Battery",       key: p => p.battery_hours_video,     fmt: (v, p) => `${v}h video · ${p.battery_hours_audio}h audio`, best: "high" },
  { label: "Water Rating",  key: p => p.water_resistance,        fmt: v => v,                     best: null   },
  { label: "Weight",        key: p => p.weight_grams,            fmt: v => `${v}g`,               best: "low"  },
  { label: "Connector",     key: p => p.connector,               fmt: v => v,                     best: null   },
  { label: "Wi-Fi",         key: p => p.wifi,                    fmt: v => v,                     best: null   },
  { label: "Dimensions",    key: p => p.height_mm,               fmt: (v, p) => `${p.height_mm} × ${p.width_mm} × ${p.depth_mm} mm`, best: "low" },
];

function winnerIdx(products, rowDef) {
  if (!rowDef.best) return new Set();
  const vals = products.map(p => rowDef.key(p));
  if (vals.some(v => typeof v !== "number" || isNaN(v))) return new Set();
  const target = rowDef.best === "high" ? Math.max(...vals) : Math.min(...vals);
  const winners = new Set();
  vals.forEach((v, i) => { if (v === target) winners.add(i); });
  return winners;
}

export default function ComparisonTable({ products, onClose }) {
  if (!products?.length) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4" onClick={onClose}>
      <div className="absolute inset-0 bg-black/40" />
      <div
        className="relative bg-white rounded-3xl w-full max-w-4xl max-h-[90vh] overflow-hidden flex flex-col"
        onClick={e => e.stopPropagation()}>

        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4" style={{ borderBottom: "1px solid #E5E5EA" }}>
          <h2 className="font-semibold text-apple-dark">Compare iPhone 17</h2>
          <button onClick={onClose} className="p-2 rounded-full hover:bg-gray-100 transition-colors">
            <X size={16} className="text-apple-dark" />
          </button>
        </div>

        {/* Table */}
        <div className="overflow-y-auto scrollbar-hide">
          <table className="w-full">
            <thead>
              <tr style={{ background: "#F5F5F7" }}>
                <th className="text-left px-6 py-4 text-xs font-semibold text-apple-light uppercase tracking-wide w-32">Spec</th>
                {products.map(p => (
                  <th key={p.model_slug} className="px-4 py-4 text-center">
                    <div className="flex flex-col items-center gap-2">
                      <img
                        src={p.image_url}
                        alt={p.display_name}
                        className="h-16 object-contain"
                        onError={e => { e.target.style.display = "none"; }}
                      />
                      <span className="text-sm font-semibold text-apple-dark leading-tight">{p.display_name}</span>
                      <span className="text-xs text-apple-light">From {fmtPrice(p.starting_price)}</span>
                    </div>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {SPEC_ROWS.map(row => {
                const winners = winnerIdx(products, row);
                return (
                  <tr key={row.label} style={{ borderBottom: "1px solid #F5F5F7" }}>
                    <td className="px-6 py-3 text-xs font-medium text-apple-light">{row.label}</td>
                    {products.map((p, i) => {
                      const rawVal = row.key(p);
                      const display = row.fmt(rawVal, p);
                      const isWinner = winners.has(i) && winners.size < products.length;
                      return (
                        <td
                          key={p.model_slug}
                          className="px-4 py-3 text-center text-sm text-apple-dark"
                          style={isWinner ? { background: "#F0FFF4", color: "#166534", fontWeight: 600 } : {}}>
                          {display}
                        </td>
                      );
                    })}
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
