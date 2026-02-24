import { useState, useMemo } from "react";
import { useCatalog } from "./hooks/useCatalog";
import NavBar from "./components/layout/NavBar";
import FilterBar from "./components/catalog/FilterBar";
import ProductGrid from "./components/catalog/ProductGrid";
import ProductModal from "./components/catalog/ProductModal";
import ChatPanel from "./components/chat/ChatPanel";
import ComparisonBar from "./components/comparison/ComparisonBar";
import ComparisonTable from "./components/comparison/ComparisonTable";
import CartDrawer from "./components/cart/CartDrawer";

const MAX_COMPARE = 3;

function applyFilter(products, filter) {
  if (!filter) return products;
  if (filter === "pro")   return products.filter(p => p.tier === "pro");
  if (filter === "standard") return products.filter(p => p.tier !== "pro");
  if (filter === "u900")  return products.filter(p => p.starting_price < 900);
  if (filter === "u1100") return products.filter(p => p.starting_price < 1100);
  return products;
}

export default function App() {
  const { products, loading } = useCatalog();

  const [activeFilter,     setActiveFilter]     = useState(null);
  const [selectedProduct,  setSelectedProduct]  = useState(null);
  const [chatOpen,         setChatOpen]         = useState(false);
  const [cartOpen,         setCartOpen]         = useState(false);
  const [cart,             setCart]             = useState([]);
  const [comparisonItems,  setComparisonItems]  = useState([]);
  const [compareTableOpen, setCompareTableOpen] = useState(false);

  const filteredProducts = useMemo(
    () => applyFilter(products, activeFilter),
    [products, activeFilter],
  );

  const comparisonSlugs = comparisonItems.map(p => p.model_slug);

  // Cart
  function handleAddToCart(product, tier) {
    const resolvedTier = tier ?? product.storage_tiers?.[0] ?? null;
    setCart(prev => [...prev, { product, tier: resolvedTier }]);
  }

  function handleRemoveFromCart(idx) {
    setCart(prev => prev.filter((_, i) => i !== idx));
  }

  // Comparison
  function handleToggleCompare(product) {
    setComparisonItems(prev => {
      if (prev.some(p => p.model_slug === product.model_slug)) {
        return prev.filter(p => p.model_slug !== product.model_slug);
      }
      if (prev.length >= MAX_COMPARE) return prev;
      return [...prev, product];
    });
  }

  return (
    <div className="min-h-screen" style={{ background: "#F5F5F7" }}>
      <NavBar
        cartCount={cart.length}
        onCartOpen={() => setCartOpen(true)}
        onChatOpen={() => setChatOpen(true)}
      />

      {/* Main content */}
      <main className="max-w-6xl mx-auto px-6 pt-20 pb-32">
        {/* Hero */}
        <div className="text-center py-12">
          <h1 className="text-4xl md:text-5xl font-semibold text-apple-dark tracking-tight">
            iPhone 17
          </h1>
          <p className="text-apple-light text-lg mt-2">
            Choose your iPhone. AI-powered recommendations grounded in 8,700+ real reviews.
          </p>
        </div>

        {/* Filters */}
        <div className="mb-6">
          <FilterBar active={activeFilter} onChange={setActiveFilter} />
        </div>

        {/* Grid */}
        <ProductGrid
          products={filteredProducts}
          loading={loading}
          onSelect={setSelectedProduct}
          onAddToCart={handleAddToCart}
          onToggleCompare={handleToggleCompare}
          comparisonSlugs={comparisonSlugs}
        />

        {/* Footer note */}
        {!loading && (
          <p className="text-center text-xs text-apple-light mt-16 pb-4">
            Prices shown are starting prices in USD. Review scores from {" "}
            <span className="font-medium">8,700+ verified customer reviews</span>.
            This is a demo app — no real purchases are processed.
          </p>
        )}
      </main>

      {/* Overlays */}
      <ProductModal
        product={selectedProduct}
        onClose={() => setSelectedProduct(null)}
        onAddToCart={(product, tier) => {
          handleAddToCart(product, tier);
          setSelectedProduct(null);
        }}
      />

      <ChatPanel
        isOpen={chatOpen}
        onClose={() => setChatOpen(false)}
      />

      <CartDrawer
        isOpen={cartOpen}
        onClose={() => setCartOpen(false)}
        items={cart}
        onRemove={handleRemoveFromCart}
      />

      <ComparisonBar
        items={comparisonItems}
        onRemove={handleToggleCompare}
        onCompare={() => setCompareTableOpen(true)}
      />

      {compareTableOpen && (
        <ComparisonTable
          products={comparisonItems}
          onClose={() => setCompareTableOpen(false)}
        />
      )}
    </div>
  );
}
