// Purely decorative, aria-hidden, fixed behind all content. Three soft
// blurred blobs in the same blue/violet/teal family as the KPI icon accents,
// so the background reads as "matching the UI" rather than an arbitrary
// color wash. Blur is applied per-shape (filter), not via a full-viewport
// backdrop-blur overlay -- that overlay was muddying everything into one
// flat gray-blue smear instead of three distinguishable soft shapes.
export function BackgroundDecoration() {
  return (
    <div aria-hidden="true" className="pointer-events-none fixed inset-0 -z-10 overflow-hidden">
      <svg
        className="animate-float-slow absolute -top-24 -right-16 h-[34rem] w-[34rem] opacity-45 blur-3xl"
        viewBox="0 0 600 600"
        xmlns="http://www.w3.org/2000/svg"
      >
        <defs>
          <linearGradient id="blob-a" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#93d2fd" />
            <stop offset="100%" stopColor="#2680ea" />
          </linearGradient>
        </defs>
        <path
          fill="url(#blob-a)"
          d="M431,320Q420,390,360,430Q300,470,235,445Q170,420,130,360Q90,300,120,235Q150,170,215,140Q280,110,345,135Q410,160,430,225Q450,290,431,320Z"
        />
      </svg>

      <svg
        className="animate-float-slower absolute top-1/3 -left-28 h-[28rem] w-[28rem] opacity-35 blur-3xl"
        viewBox="0 0 600 600"
        xmlns="http://www.w3.org/2000/svg"
      >
        <defs>
          <linearGradient id="blob-b" x1="0%" y1="100%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="#c4b5fd" />
            <stop offset="100%" stopColor="#8b5cf6" />
          </linearGradient>
        </defs>
        <path
          fill="url(#blob-b)"
          d="M410,300Q400,380,325,415Q250,450,180,410Q110,370,105,290Q100,210,165,165Q230,120,305,135Q380,150,405,220Q430,290,410,300Z"
        />
      </svg>

      <svg
        className="animate-float-slow absolute -bottom-32 left-1/4 h-[26rem] w-[26rem] opacity-40 blur-3xl"
        viewBox="0 0 600 600"
        xmlns="http://www.w3.org/2000/svg"
      >
        <defs>
          <linearGradient id="blob-c" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#99f6e4" />
            <stop offset="100%" stopColor="#14b8a6" />
          </linearGradient>
        </defs>
        <path
          fill="url(#blob-c)"
          d="M420,290Q410,360,345,400Q280,440,215,405Q150,370,135,300Q120,230,175,180Q230,130,300,145Q370,160,405,220Q440,280,420,290Z"
        />
      </svg>
    </div>
  );
}
