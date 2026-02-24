import { X, ShoppingBag, Trash2 } from "lucide-react";
import { fmtPrice } from "../../utils/formatters";

export default function CartDrawer({ isOpen, onClose, items, onRemove }) {
  const subtotal = items.reduce((sum, item) => sum + (item.tier?.price_usd ?? item.product.starting_price), 0);

  return (
    <>
      {/* Backdrop */}
      {isOpen && <div className="fixed inset-0 bg-black/20 z-40" onClick={onClose} />}

      {/* Drawer */}
      <div
        className="fixed top-0 right-0 bottom-0 z-50 flex flex-col bg-white shadow-2xl transition-transform duration-300"
        style={{
          width: "min(400px, 100vw)",
          transform: isOpen ? "translateX(0)" : "translateX(100%)",
          borderLeft: "1px solid #E5E5EA",
        }}>

        {/* Header */}
        <div className="flex items-center justify-between px-5 py-4" style={{ borderBottom: "1px solid #E5E5EA" }}>
          <div className="flex items-center gap-2">
            <ShoppingBag size={16} className="text-apple-dark" />
            <h2 className="font-semibold text-sm text-apple-dark">Bag</h2>
            {items.length > 0 && (
              <span className="text-xs text-white px-1.5 py-0.5 rounded-full" style={{ background: "#0071E3" }}>
                {items.length}
              </span>
            )}
          </div>
          <button onClick={onClose} className="p-1.5 rounded-full hover:bg-gray-100 transition-colors">
            <X size={16} className="text-apple-dark" />
          </button>
        </div>

        {/* Items */}
        <div className="flex-1 overflow-y-auto px-4 py-4 scrollbar-hide">
          {items.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full gap-3">
              <ShoppingBag size={40} className="text-apple-light opacity-30" />
              <p className="text-sm text-apple-light">Your bag is empty</p>
            </div>
          ) : (
            <div className="space-y-3">
              {items.map((item, i) => (
                <div
                  key={i}
                  className="flex items-center gap-3 p-3 rounded-2xl"
                  style={{ border: "1px solid #E5E5EA" }}>
                  <img
                    src={item.product.image_url}
                    alt={item.product.display_name}
                    className="w-14 h-14 object-contain flex-shrink-0"
                    onError={e => { e.target.style.display = "none"; }}
                  />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-apple-dark truncate">{item.product.display_name}</p>
                    {item.tier && (
                      <p className="text-xs text-apple-light">{item.tier.capacity}</p>
                    )}
                    <p className="text-sm font-semibold text-apple-dark mt-0.5">
                      {fmtPrice(item.tier?.price_usd ?? item.product.starting_price)}
                    </p>
                  </div>
                  <button
                    onClick={() => onRemove(i)}
                    className="p-1.5 rounded-full hover:bg-gray-100 transition-colors flex-shrink-0">
                    <Trash2 size={13} className="text-apple-light" />
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Footer */}
        {items.length > 0 && (
          <div className="px-5 py-5" style={{ borderTop: "1px solid #E5E5EA" }}>
            <div className="flex justify-between text-sm mb-4">
              <span className="text-apple-light">Subtotal</span>
              <span className="font-semibold text-apple-dark">{fmtPrice(subtotal)}</span>
            </div>
            <button
              className="w-full py-3 rounded-full text-sm font-semibold text-white"
              style={{ background: "#0071E3" }}
              onClick={() => alert("Checkout is a mockup — no real purchase!")}>
              Check Out
            </button>
            <p className="text-center text-[10px] text-apple-light mt-2">This is a demo. No real purchase will be made.</p>
          </div>
        )}
      </div>
    </>
  );
}
