import Image from "next/image";
import { hltBranding } from "@/lib/hltBranding";

type MasteryIconProps = {
  className?: string;
  size?: number;
};

export default function MasteryIcon({ className = "", size = 44 }: MasteryIconProps) {
  return (
    <span
      className={`inline-flex items-center justify-center overflow-hidden rounded-[22%] bg-white shadow-[0_10px_24px_rgba(10,10,11,0.24)] ring-1 ring-white/20 ${className}`}
      style={{ width: size, height: size }}
      aria-hidden="true"
    >
      <Image
        src={hltBranding.icon}
        alt=""
        width={size}
        height={size}
        className="h-full w-full object-cover"
        priority
      />
    </span>
  );
}
