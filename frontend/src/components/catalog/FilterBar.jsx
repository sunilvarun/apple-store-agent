const FILTERS = [
  { label: "All iPhones",  value: null },
  { label: "Pro",          value: "pro" },
  { label: "Standard",     value: "standard" },
  { label: "Under $900",   value: "u900" },
  { label: "Under $1100",  value: "u1100" },
];

export default function FilterBar({ active, onChange }) {
  return (
    <div className="flex gap-2 overflow-x-auto scrollbar-hide py-1">
      {FILTERS.map(f => {
        const isActive = active === f.value;
        return (
          <button key={f.label} onClick={() => onChange(f.value)}
            className="whitespace-nowrap px-4 py-1.5 rounded-full text-sm font-medium transition-all"
            style={{
              background: isActive ? "#1D1D1F" : "#FFFFFF",
              color:      isActive ? "#FFFFFF"  : "#1D1D1F",
              border:     "1px solid #D2D2D7",
            }}>
            {f.label}
          </button>
        );
      })}
    </div>
  );
}
