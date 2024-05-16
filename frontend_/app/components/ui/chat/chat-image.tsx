import Image from "next/image";
import { type ImageData } from "./index";

export function ChatImage({ data }: { data: ImageData }) {
  return (
    <div className="rounded-md max-w-[200px] shadow-md">
      <Image
        src={data.url}
        width={0}
        height={0}
        sizes="100vw"
        style={{ width: "100%", height: "auto" }}
        alt=""
      />
    </div>
  );
}
