interface HotelIconProps {
  className?: string;
}

export function HotelIcon({ className }: HotelIconProps) {
  return (
    <svg viewBox="0 0 24 24" fill="none" className={className} xmlns="http://www.w3.org/2000/svg">
      <path
        d="M4 21V5.5C4 4.67 4.67 4 5.5 4h5C11.33 4 12 4.67 12 5.5V21"
        stroke="currentColor"
        strokeWidth="1.6"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <path
        d="M12 10.5h5.5c1.1 0 2 .9 2 2V21"
        stroke="currentColor"
        strokeWidth="1.6"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <path d="M2.5 21h19" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
      <rect x="6" y="7" width="1.8" height="1.8" rx="0.3" fill="currentColor" />
      <rect x="9.2" y="7" width="1.8" height="1.8" rx="0.3" fill="currentColor" />
      <rect x="6" y="10.4" width="1.8" height="1.8" rx="0.3" fill="currentColor" />
      <rect x="9.2" y="10.4" width="1.8" height="1.8" rx="0.3" fill="currentColor" />
      <rect x="6" y="13.8" width="1.8" height="1.8" rx="0.3" fill="currentColor" />
      <rect x="9.2" y="13.8" width="1.8" height="1.8" rx="0.3" fill="currentColor" />
      <rect x="14.3" y="13.4" width="1.8" height="1.8" rx="0.3" fill="currentColor" />
      <rect x="17.5" y="13.4" width="1.8" height="1.8" rx="0.3" fill="currentColor" />
      <path d="M9.5 21v-3.2c0-.5.4-.9.9-.9h1.2c.5 0 .9.4.9.9V21" stroke="currentColor" strokeWidth="1.6" />
    </svg>
  );
}
