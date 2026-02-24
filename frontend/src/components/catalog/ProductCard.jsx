import { Plus, BarChart2 } from "lucide-react";
import { fmtPrice } from "../../utils/formatters";

const COLOR_SWATCHES = {
  "Black Titanium": "#3A3A3C", "White Titanium": "#E8E3D9",
  "Natural Titanium": "#B5A99A", "Desert Titanium": "#C4A882",
  "Black": "#1D1D1F", "White": "#F5F5F0", "Pink": "#F2C5C0",
  "Teal": "#4A9E9A", "Ultramarine": "#3B4BC8", "Sky Blue": "#87CEEB",
  "Rose": "#E8A0A0",
};

export default function ProductCard({ product, onSelect, onAddToCart, onToggleCompare, inComparison }) {
  const tierBadge = product.tier === "pro"
    ? { label: "Pro", bg: "#1D1D1F", color: "#fff" }
    : null;

  return (
    <div
      onClick={() => onSelect(product)}
      className="bg-white rounded-3xl p-6 cursor-pointer group transition-all duration-300 hover:shadow-xl"
      style={{ border: "1px solid #E5E5EA" }}>

      {/* Tier badge */}
      <div className="flex justify-between items-start mb-4">
        {tierBadge
          ? <span className="text-[11px] font-semibold px-2.5 py-1 rounded-full" style={{ background: tierBadge.bg, color: tierBadge.color }}>{tierBadge.label}</span>
          : <span />}
        <button
          onClick={e => { e.stopPropagation(); onToggleCompare(product); }}
          className="p-1.5 rounded-full transition-colors"
          style={{ background: inComparison ? "#0071E3" : "#F5F5F7", color: inComparison ? "#fff" : "#1D1D1F" }}
          title={inComparison ? "Remove from comparison" : "Add to comparison"}>
          <BarChart2 size={13} />
        </button>
      </div>

      {/* Product image */}
      <div className="flex justify-center mb-6 h-48">
        <img
          src={product.image_url}
          alt={product.display_name}
          className="h-full object-contain transition-transform duration-300 group-hover:scale-105"
          onError={e => { e.target.style.display = "none"; }}
        />
      </div>

      {/* Name + price */}
      <div className="mb-3">
        <h3 className="font-semibold text-base text-apple-dark leading-tight">{product.display_name}</h3>
        <p className="text-apple-light text-sm mt-0.5">
          From {fmtPrice(product.starting_price)}
        </p>
      </div>

      {/* Key specs */}
      <div className="text-xs text-apple-light space-y-1 mb-4">
        <div>{product.chip} chip</div>
        <div>{product.display_size}" · {product.rear_cameras.length}-camera system · {product.max_optical_zoom} zoom</div>
        <div>{product.battery_hours_video}h video · {product.weight_grams}g</div>
      </div>

      {/* Color swatches */}
      <div className="flex gap-1.5 mb-5">
        {product.colors.slice(0, 5).map(c => (
          <div key={c} className="w-4 h-4 rounded-full border border-gray-200" style={{ background: COLOR_SWATCHES[c] || "#ccc" }} title={c} />
        ))}
      </div>

      {/* CTA */}
      <button
        onClick={e => { e.stopPropagation(); onAddToCart(product); }}
        className="w-full py-2 rounded-full text-sm font-medium text-white transition-colors"
        style={{ background: "#0071E3" }}
        onMouseEnter={e => e.target.style.background = "#0077ED"}
        onMouseLeave={e => e.target.style.background = "#0071E3"}>
        <Plus size={13} className="inline mr-1" />
        Add to Bag
      </button>
    </div>
  );
}
