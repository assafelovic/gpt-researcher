import Image from "next/image";
import SourceCard from "./elements/SourceCard";

export default function Sources({
  sources,
}: {
  sources: { name: string; url: string }[];
}) {
  return (
    <div className="container h-auto w-full shrink-0 rounded-lg border border-solid border-[#C2C2C2] bg-gray-800 shadow-md p-5">
      <div className="flex items-start gap-4 pb-3 lg:pb-3.5">
        <Image src="/img/browser.svg" alt="footer" width={24} height={24} />
        <h3 className="text-base font-bold uppercase leading-[152.5%] text-white">
          sources{" "}
        </h3>
      </div>
      <div className="overflow-y-auto max-h-[250px] scrollbar-thin scrollbar-thumb-gray-600 scrollbar-track-gray-300">
        <div className="flex w-full max-w-[890px] flex-wrap content-center items-center gap-[15px] pb-2">
          {sources.length > 0 ? (
            sources.map((source) => (
              <SourceCard source={source} key={source.url} />
            ))
          ) : (
            <>
              <div className="h-20 w-[260px] max-w-sm animate-pulse rounded-md bg-gray-300" />
              <div className="h-20 w-[260px] max-w-sm animate-pulse rounded-md bg-gray-300" />
              <div className="h-20 w-[260px] max-w-sm animate-pulse rounded-md bg-gray-300" />
              <div className="h-20 w-[260px] max-w-sm animate-pulse rounded-md bg-gray-300" />
              <div className="h-20 w-[260px] max-w-sm animate-pulse rounded-md bg-gray-300" />
              <div className="h-20 w-[260px] max-w-sm animate-pulse rounded-md bg-gray-300" />
            </>
          )}
        </div>
      </div>
    </div>
  );
}
