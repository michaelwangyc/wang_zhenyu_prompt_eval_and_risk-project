export default function Loading() {
  return (
    <div className="min-h-screen bg-[#FDF6EC] dark:bg-[#0F2027] flex items-center justify-center relative overflow-hidden">
      {/* Loading Content */}
      <div className="relative flex flex-col items-center gap-8">
        {/* Pixel Red Cross Spinner */}
        <div className="relative">
          <div className="w-20 h-20 rounded-2xl border-4 border-[#2A9D8F]/30 border-t-[#2A9D8F] animate-spin"></div>
          <div className="absolute inset-0 flex items-center justify-center">
            <svg viewBox="0 0 40 40" className="w-10 h-10 animate-pulse">
              <rect x="15" y="5" width="10" height="30" rx="2" fill="#E63946" />
              <rect x="5" y="15" width="30" height="10" rx="2" fill="#E63946" />
            </svg>
          </div>
        </div>

        {/* Loading Text */}
        <div className="flex flex-col items-center gap-3">
          <p className="font-display text-xl text-[#1D3557] dark:text-white">
            Loading <span className="text-[#2A9D8F]">MaterniFlow</span>...
          </p>
          <div className="flex gap-1.5">
            <span className="w-3 h-3 bg-[#2A9D8F] rounded-md animate-bounce" style={{ animationDelay: "0ms" }}></span>
            <span className="w-3 h-3 bg-[#F4A261] rounded-md animate-bounce" style={{ animationDelay: "150ms" }}></span>
            <span className="w-3 h-3 bg-[#E63946] rounded-md animate-bounce" style={{ animationDelay: "300ms" }}></span>
          </div>
        </div>
      </div>
    </div>
  )
}
