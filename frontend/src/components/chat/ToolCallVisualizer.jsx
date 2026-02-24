import { Loader2 } from "lucide-react";
import { TOOL_LABELS } from "../../utils/constants";

export default function ToolCallVisualizer({ tool }) {
  if (!tool) return null;
  return (
    <div className="flex items-center gap-2 px-4 py-2 mx-4 mb-2 rounded-full text-xs text-apple-light"
      style={{ background: "#F5F5F7", width: "fit-content" }}>
      <Loader2 size={12} className="animate-spin" style={{ color: "#0071E3" }} />
      <span>{TOOL_LABELS[tool] || tool}…</span>
    </div>
  );
}
