import Image from "next/image";
import ImagesAlbum from '../Images/ImagesAlbum';

interface ImageSectionProps {
  metadata: any;
}

const ImageSection = ({ metadata }: ImageSectionProps) => {
  return (
    <div className="container h-auto w-full shrink-0 rounded-lg border border-solid border-[#C2C2C2] bg-gray-800 shadow-md p-5">
      <div className="flex items-start gap-4 pb-3 lg:pb-3.5">
        <Image src="/img/image.svg" alt="images" width={24} height={24} />
        <h3 className="text-base font-bold uppercase leading-[152.5%] text-white">
          Related Images
        </h3>
      </div>
      <div className="overflow-y-auto max-h-[500px] scrollbar-thin scrollbar-thumb-gray-600 scrollbar-track-gray-300">
        <ImagesAlbum images={metadata} />
      </div>
    </div>
  );
};

export default ImageSection; 