// Purely decorative, aria-hidden, fixed behind all content. An actual
// illustrated blob shape (not just blurred circles) plus slow drift so the
// page doesn't read as flat/static.
export function BackgroundDecoration() {
  return (
    <div aria-hidden="true" className="pointer-events-none fixed inset-0 -z-10 overflow-hidden">
      <svg
        className="animate-float-slow absolute -top-32 -right-24 h-[36rem] w-[36rem] opacity-60"
        viewBox="0 0 600 600"
        xmlns="http://www.w3.org/2000/svg"
      >
        <defs>
          <linearGradient id="blob-a" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#bfe3fe" />
            <stop offset="100%" stopColor="#93d2fd" />
          </linearGradient>
        </defs>
        <path
          fill="url(#blob-a)"
          d="M431,320Q420,390,360,430Q300,470,235,445Q170,420,130,360Q90,300,120,235Q150,170,215,140Q280,110,345,135Q410,160,430,225Q450,290,431,320Z"
        />
      </svg>

      <svg
        className="animate-float-slower absolute top-1/3 -left-32 h-[30rem] w-[30rem] opacity-50"
        viewBox="0 0 600 600"
        xmlns="http://www.w3.org/2000/svg"
      >
        <defs>
          <linearGradient id="blob-b" x1="0%" y1="100%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="#a5f3fc" />
            <stop offset="100%" stopColor="#c7d2fe" />
          </linearGradient>
        </defs>
        <path
          fill="url(#blob-b)"
          d="M410,300Q400,380,325,415Q250,450,180,410Q110,370,105,290Q100,210,165,165Q230,120,305,135Q380,150,405,220Q430,290,410,300Z"
        />
      </svg>

      <svg
        className="animate-float-slow absolute -bottom-40 left-1/4 h-96 w-96 opacity-40"
        viewBox="0 0 600 600"
        xmlns="http://www.w3.org/2000/svg"
      >
        <defs>
          <linearGradient id="blob-c" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#99f6e4" />
            <stop offset="100%" stopColor="#bfe3fe" />
          </linearGradient>
        </defs>
        <path
          fill="url(#blob-c)"
          d="M420,290Q410,360,345,400Q280,440,215,405Q150,370,135,300Q120,230,175,180Q230,130,300,145Q370,160,405,220Q440,280,420,290Z"
        />
      </svg>

      <div className="absolute inset-0 backdrop-blur-3xl" />
    </div>
  );
}
