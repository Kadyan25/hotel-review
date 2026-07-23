import { useState } from "react";
import { HotelIcon } from "./icons/HotelIcon";

interface PropertyThumbnailProps {
  src: string | null;
  alt: string;
  accentBg: string;
  accentIcon: string;
  className: string;
  iconClassName: string;
}

// Hotlinked directly from Booking.com's own CDN -- these signed URLs (the
// `k=` token) can expire, so a load failure falls back to the icon badge
// rather than showing a broken image.
export function PropertyThumbnail({ src, alt, accentBg, accentIcon, className, iconClassName }: PropertyThumbnailProps) {
  const [failed, setFailed] = useState(false);

  if (!src || failed) {
    return (
      <div className={`flex items-center justify-center rounded-lg ${accentBg} ${className}`}>
        <HotelIcon className={`${accentIcon} ${iconClassName}`} />
      </div>
    );
  }

  return (
    <img
      src={src}
      alt={alt}
      onError={() => setFailed(true)}
      className={`rounded-lg object-cover ${className}`}
    />
  );
}
