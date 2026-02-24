import ProductCard from "./ProductCard";

function Skeleton() {
  return (
    <div className="bg-white rounded-3xl p-6 animate-pulse" style={{ border: "1px solid #E5E5EA" }}>
      <div className="h-48 bg-gray-100 rounded-2xl mb-6" />
      <div className="h-4 bg-gray-100 rounded w-3/4 mb-2" />
      <div className="h-3 bg-gray-100 rounded w-1/2 mb-4" />
      <div className="h-3 bg-gray-100 rounded w-full mb-1" />
      <div className="h-3 bg-gray-100 rounded w-2/3 mb-6" />
      <div className="h-9 bg-gray-100 rounded-full" />
    </div>
  );
}

export default function ProductGrid({ products, loading, onSelect, onAddToCart, onToggleCompare, comparisonSlugs }) {
  if (loading) {
    return (
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        {[1, 2, 3, 4].map(i => <Skeleton key={i} />)}
      </div>
    );
  }

  if (!products.length) {
    return (
      <div className="text-center py-20 text-apple-light">
        <p className="text-lg">No iPhones match your filters.</p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
      {products.map(p => (
        <ProductCard
          key={p.model_slug}
          product={p}
          onSelect={onSelect}
          onAddToCart={onAddToCart}
          onToggleCompare={onToggleCompare}
          inComparison={comparisonSlugs.includes(p.model_slug)}
        />
      ))}
    </div>
  );
}
