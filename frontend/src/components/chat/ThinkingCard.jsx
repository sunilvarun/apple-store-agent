import { useState } from "react";
import { ChevronDown, Check, Loader2 } from "lucide-react";

// One-line description shown when the card is expanded
const TOOL_DESCRIPTIONS = {
  extract_preferences:
    "Claude translated your message into a structured profile. This drives everything that follows — the catalog filter, the ranker, and the final recommendation.",
  search_catalog:
    "The catalog was filtered by price, series, and any feature requirements to narrow down candidates before scoring.",
  get_product_details:
    "Full specs and reviewer evidence were pulled for this model to support a detailed answer.",
  rank_iphones:
    "Every candidate was scored using a blend of Apple specs (60%) and real reviewer sentiment (40%), weighted by your stated priorities.",
  compare_products:
    "A side-by-side comparison was run across specs and real reviewer data for each model.",
};

// Human-readable header shown in the collapsed pill
const TOOL_HEADERS = {
  extract_preferences: "🧠 Read your priorities",
  search_catalog:      "🔍 Searched the catalog",
  get_product_details: "📋 Loaded specs + reviews",
  rank_iphones:        "📊 Scored the candidates",
  compare_products:    "⚖️ Ran comparison",
};

// ─── Preference card content ──────────────────────────────────────────────────

function PreferencesDetail({ input }) {
  const { budget_max, priorities = {}, constraints = {}, apps = [] } = input ?? {};

  // Sort priorities by weight descending
  const sortedPriorities = Object.entries(priorities)
    .filter(([, w]) => w > 0)
    .sort(([, a], [, b]) => b - a);

  const PRIORITY_COLORS = {
    camera:      { bg: "#E8F4FD", text: "#0071E3" },
    battery:     { bg: "#E8F7EE", text: "#1D8348" },
    performance: { bg: "#FEF3E2", text: "#B7600A" },
    display:     { bg: "#F3E8FF", text: "#7B2FBE" },
    weight:      { bg: "#FDE8EC", text: "#C0392B" },
    value:       { bg: "#E8F7F7", text: "#148F77" },
    heating:     { bg: "#FEF9E7", text: "#9A7D0A" },
    durability:  { bg: "#F2F3F4", text: "#5D6D7E" },
  };

  return (
    <div className="space-y-3 pt-2">
      <p className="text-[11px] text-apple-light leading-relaxed">
        {TOOL_DESCRIPTIONS.extract_preferences}
      </p>

      <div className="space-y-2 text-xs">
        {/* Budget */}
        <div className="flex items-start gap-3">
          <span className="text-apple-light w-20 flex-shrink-0 pt-0.5">Budget</span>
          <span className="text-apple-dark font-medium">
            {budget_max ? `Up to $${budget_max.toLocaleString()}` : "No limit mentioned"}
          </span>
        </div>

        {/* Priorities */}
        {sortedPriorities.length > 0 && (
          <div className="flex items-start gap-3">
            <span className="text-apple-light w-20 flex-shrink-0 pt-1">Priorities</span>
            <div className="flex flex-wrap gap-1.5">
              {sortedPriorities.map(([aspect]) => {
                const color = PRIORITY_COLORS[aspect] ?? { bg: "#F5F5F7", text: "#1D1D1F" };
                return (
                  <span
                    key={aspect}
                    className="px-2 py-0.5 rounded-full text-[11px] font-medium capitalize"
                    style={{ background: color.bg, color: color.text }}>
                    {aspect}
                  </span>
                );
              })}
            </div>
          </div>
        )}

        {/* Screen size */}
        {constraints.size_preference && constraints.size_preference !== "any" && (
          <div className="flex items-start gap-3">
            <span className="text-apple-light w-20 flex-shrink-0 pt-0.5">Screen size</span>
            <span className="text-apple-dark font-medium capitalize">
              {constraints.size_preference} preferred
            </span>
          </div>
        )}

        {/* Min storage */}
        {constraints.min_storage_gb && (
          <div className="flex items-start gap-3">
            <span className="text-apple-light w-20 flex-shrink-0 pt-0.5">Storage</span>
            <span className="text-apple-dark font-medium">
              At least {constraints.min_storage_gb}GB
            </span>
          </div>
        )}

        {/* Apps */}
        {apps.length > 0 && (
          <div className="flex items-start gap-3">
            <span className="text-apple-light w-20 flex-shrink-0 pt-0.5">Apps</span>
            <span className="text-apple-dark font-medium">{apps.join(", ")}</span>
          </div>
        )}

        {/* If nothing meaningful was extracted */}
        {sortedPriorities.length === 0 && !budget_max && apps.length === 0 && (
          <p className="text-apple-light italic">
            No specific constraints detected — Claude will consider all models.
          </p>
        )}
      </div>
    </div>
  );
}

// ─── Main ThinkingCard ────────────────────────────────────────────────────────

export default function ThinkingCard({ tool, input, result }) {
  const [open, setOpen] = useState(false);
  const done = result !== null;
  const header = TOOL_HEADERS[tool] ?? tool;

  // For now only extract_preferences has a rich detail view
  // Other tools fall back to a generic description
  const renderDetail = () => {
    if (tool === "extract_preferences") {
      return <PreferencesDetail input={input} />;
    }
    return (
      <p className="text-[11px] text-apple-light leading-relaxed pt-2">
        {TOOL_DESCRIPTIONS[tool] ?? "This step gathered data to support the recommendation."}
      </p>
    );
  };

  return (
    <div
      className="mx-0 mb-2 rounded-2xl overflow-hidden text-xs"
      style={{ border: "1px solid #E5E5EA", background: "#FAFAFA" }}>

      {/* Collapsed header — always visible */}
      <button
        onClick={() => setOpen(v => !v)}
        className="w-full flex items-center justify-between px-4 py-2.5 hover:bg-gray-50 transition-colors"
      >
        <div className="flex items-center gap-2">
          {done ? (
            <span className="flex items-center justify-center w-4 h-4 rounded-full" style={{ background: "#E8F7EE" }}>
              <Check size={9} style={{ color: "#1D8348" }} />
            </span>
          ) : (
            <Loader2 size={12} className="animate-spin" style={{ color: "#0071E3" }} />
          )}
          <span className="font-medium text-apple-dark">{header}</span>
        </div>
        <ChevronDown
          size={13}
          className="transition-transform text-apple-light"
          style={{ transform: open ? "rotate(180deg)" : "rotate(0deg)" }}
        />
      </button>

      {/* Expanded content */}
      {open && (
        <div className="px-4 pb-4" style={{ borderTop: "1px solid #E5E5EA" }}>
          {renderDetail()}
        </div>
      )}
    </div>
  );
}
