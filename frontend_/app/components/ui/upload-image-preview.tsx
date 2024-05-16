import { XCircleIcon } from "lucide-react";
import Image from "next/image";
import { cn } from "./lib/utils";

export default function UploadImagePreview({
  url,
  onRemove,
}: {
  url: string;
  onRemove: () => void;
}) {
  return (
    <div className="relative w-20 h-20 group">
      <Image
        src={url}
        alt="Uploaded image"
        fill
        className="object-cover w-full h-full rounded-xl hover:brightness-75"
      />
      <div
        className={cn(
          "absolute -top-2 -right-2 w-6 h-6 z-10 bg-gray-500 text-white rounded-full hidden group-hover:block",
        )}
      >
        <XCircleIcon
          className="w-6 h-6 bg-gray-500 text-white rounded-full"
          onClick={onRemove}
        />
      </div>
    </div>
  );
}
