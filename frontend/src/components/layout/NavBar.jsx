import { ShoppingBag, MessageCircle, Search } from "lucide-react";

export default function NavBar({ cartCount, onCartOpen, onChatOpen }) {
  return (
    <nav className="fixed top-0 left-0 right-0 z-50 h-12"
      style={{ background: "rgba(255,255,255,0.85)", backdropFilter: "saturate(180%) blur(20px)", borderBottom: "1px solid rgba(0,0,0,0.08)" }}>
      <div className="max-w-6xl mx-auto px-6 h-full flex items-center justify-between">

        {/* Apple logo */}
        <svg viewBox="0 0 814 1000" className="w-5 h-5 fill-current text-apple-dark" aria-label="Apple">
          <path d="M788.1 340.9c-5.8 4.5-108.2 62.2-108.2 190.5 0 148.4 130.3 200.9 134.2 202.2-.6 3.2-20.7 71.9-68.7 141.9-42.8 61.6-87.5 123.1-155.5 123.1s-85.5-39.5-164-39.5c-76.5 0-103.7 40.8-165.9 40.8s-105-57.8-155.5-127.4C46 790.7 0 663 0 541.8c0-207.5 135.4-317.1 269-317.1 71 0 130.5 46.4 175 46.4 42.9 0 109.7-49 192.5-49 30.8 0 134.1 2.8 202.8 113.4zm-234-181.5c31.1-36.9 53.1-88.1 53.1-139.3 0-7.1-.6-14.3-1.9-20.1-50.6 1.9-110.8 33.7-147.1 75.8-28.5 32.4-55.1 83.6-55.1 135.5 0 7.8 1.3 15.6 1.9 18.1 3.2.6 8.4 1.3 13.6 1.3 45.4 0 102.5-30.4 135.5-71.3z"/>
        </svg>

        {/* Center nav links */}
        <div className="hidden md:flex gap-8 text-xs text-apple-dark">
          {["Store", "Mac", "iPad", "iPhone", "Watch", "AirPods", "Support"].map(l => (
            <a key={l} href="#" className="hover:text-apple-light transition-colors">{l}</a>
          ))}
        </div>

        {/* Right icons */}
        <div className="flex items-center gap-4">
          <Search size={16} className="cursor-pointer text-apple-dark hover:text-apple-light transition-colors" />

          <button onClick={onChatOpen}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium text-white transition-colors"
            style={{ background: "#0071E3" }}>
            <MessageCircle size={13} />
            <span>iPhone Advisor</span>
          </button>

          <button onClick={onCartOpen} className="relative text-apple-dark hover:text-apple-light transition-colors">
            <ShoppingBag size={18} />
            {cartCount > 0 && (
              <span className="absolute -top-1.5 -right-1.5 w-4 h-4 rounded-full text-white text-[9px] flex items-center justify-center font-semibold"
                style={{ background: "#0071E3" }}>
                {cartCount}
              </span>
            )}
          </button>
        </div>
      </div>
    </nav>
  );
}
