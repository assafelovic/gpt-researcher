import Image from "next/image";
import { useState, useMemo } from "react";

const SourceCard = ({ source }: { source: { name: string; url: string } }) => {
  const [imageSrc, setImageSrc] = useState(`https://www.google.com/s2/favicons?domain=${source.url}&sz=128`);

  const handleImageError = () => {
    setImageSrc("/img/globe.svg");
  };
  
  // Extract and format the domain from the URL
  const formattedUrl = useMemo(() => {
    try {
      const urlObj = new URL(source.url);
      return urlObj.hostname.replace(/^www\./, '');
    } catch (e) {
      // If URL parsing fails, use the original URL but trim it
      return source.url.length > 50 ? source.url.substring(0, 50) + '...' : source.url;
    }
  }, [source.url]);

  return (
    <div className="flex h-[79px] w-full items-center gap-3 rounded-lg border border-solid border-gray-700/30 bg-gray-800/30 backdrop-blur-sm shadow-sm px-3 py-2 md:w-auto hover:border-teal-500/30 transition-colors duration-200">
      
        <img
          src={imageSrc}
          alt={source.url}
          className="p-1"
          width={44}
          height={44}
          onError={handleImageError}  // Update src on error
        />
      
      <div className="flex max-w-[192px] flex-col justify-center gap-[7px]">
        <h6 className="line-clamp-2 text-sm font-medium leading-[normal] text-white">
          {source.name}
        </h6>
        <a
          target="_blank"
          rel="noopener noreferrer"
          href={source.url}
          className="truncate text-sm font-light text-gray-300/60 hover:text-teal-300/80 transition-colors"
          title={source.url}
        >
          {formattedUrl}
        </a>
      </div>
    </div>
  );
};

export default SourceCard;
