export const fmtPrice = (n) =>
  new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 0 }).format(n);

export const fmtScore = (n) => (n * 100).toFixed(0);

export const sentimentLabel = (score) => {
  if (score >= 0.65) return { label: "Very Positive", color: "#34C759" };
  if (score >= 0.55) return { label: "Positive",      color: "#30D158" };
  if (score >= 0.45) return { label: "Mixed",         color: "#FF9F0A" };
  return                     { label: "Negative",      color: "#FF3B30" };
};
