import { useState, useEffect } from "react";
import { X, ShoppingBag } from "lucide-react";
import { fmtPrice, sentimentLabel } from "../../utils/formatters";

export default function ProductModal({ product, onClose, onAddToCart }) {
  const [tier, setTier] = useState(product?.storage_tiers?.[0]);

  useEffect(() => { setTier(product?.storage_tiers?.[0]); }, [product]);
  useEffect(() => {
    const handler = e => { if (e.key === "Escape") onClose(); };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [onClose]);

  if (!product) return null;

  const specs = [
    ["Chip",             product.chip],
    ["Display",          `${product.display_size}" · ${product.display_type}`],
    ["Resolution",       product.display_resolution],
    ["Rear Cameras",     `${product.rear_cameras.length}-camera system`],
    ["Optical Zoom",     product.max_optical_zoom],
    ["Video",            product.video_max],
    ["Battery",          `${product.battery_hours_video}h video · ${product.battery_hours_audio}h audio`],
    ["Water Resistance", product.water_resistance],
    ["Connector",        product.connector],
    ["Wi-Fi",            product.wifi],
    ["Weight",           `${product.weight_grams}g`],
    ["Dimensions",       `${product.height_mm} × ${product.width_mm} × ${product.depth_mm} mm`],
  ];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4" onClick={onClose}>
      <div className="absolute inset-0 bg-black/40" />
      <div
        className="relative bg-white rounded-3xl w-full max-w-3xl max-h-[90vh] overflow-hidden flex flex-col md:flex-row"
        onClick={e => e.stopPropagation()}>

        {/* Close */}
        <button onClick={onClose} className="absolute top-4 right-4 z-10 p-2 rounded-full hover:bg-gray-100 transition-colors">
          <X size={18} className="text-apple-dark" />
        </button>

        {/* Left: image */}
        <div className="md:w-2/5 p-8 flex flex-col items-center justify-center" style={{ background: "#F5F5F7" }}>
          <img src={product.image_url} alt={product.display_name}
            className="h-56 object-contain"
            onError={e => { e.target.style.display = "none"; }} />
          <h2 className="text-xl font-semibold text-apple-dark mt-4 text-center">{product.display_name}</h2>
          <p className="text-apple-light text-sm mt-1">
            {tier ? fmtPrice(tier.price_usd) : fmtPrice(product.starting_price)}
          </p>
        </div>

        {/* Right: details */}
        <div className="md:w-3/5 overflow-y-auto scrollbar-hide p-6">

          {/* Storage selector */}
          <div className="mb-6">
            <p className="text-xs font-semibold text-apple-dark mb-2 uppercase tracking-wide">Storage</p>
            <div className="flex gap-2 flex-wrap">
              {product.storage_tiers.map(t => (
                <button key={t.capacity}
                  onClick={() => setTier(t)}
                  className="px-4 py-2 rounded-full text-sm font-medium transition-all"
                  style={{
                    border:      tier?.capacity === t.capacity ? "2px solid #0071E3" : "1.5px solid #D2D2D7",
                    color:       tier?.capacity === t.capacity ? "#0071E3" : "#1D1D1F",
                    background:  "#fff",
                  }}>
                  {t.capacity} · {fmtPrice(t.price_usd)}
                </button>
              ))}
            </div>
          </div>

          {/* Spec table */}
          <div className="mb-6">
            <p className="text-xs font-semibold text-apple-dark mb-3 uppercase tracking-wide">Specifications</p>
            <div className="space-y-2">
              {specs.map(([label, value]) => (
                <div key={label} className="flex gap-3 text-sm py-1.5" style={{ borderBottom: "1px solid #F5F5F7" }}>
                  <span className="text-apple-light w-32 flex-shrink-0">{label}</span>
                  <span className="text-apple-dark">{value}</span>
                </div>
              ))}
            </div>
          </div>

          {/* CTA */}
          <button
            onClick={() => { onAddToCart(product, tier); onClose(); }}
            className="w-full py-3 rounded-full text-sm font-semibold text-white flex items-center justify-center gap-2"
            style={{ background: "#0071E3" }}>
            <ShoppingBag size={15} />
            Add to Bag · {tier ? fmtPrice(tier.price_usd) : fmtPrice(product.starting_price)}
          </button>
        </div>
      </div>
    </div>
  );
}
