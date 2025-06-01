import React, { useState, useEffect } from 'react';
import ImageModal from './ImageModal';

type ImageType = any; // Simple type definition to avoid errors

interface ImagesAlbumProps {
  images: ImageType[];
}

export default function ImagesAlbum({ images }: ImagesAlbumProps) {
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [selectedImage, setSelectedImage] = useState(null);
    const [selectedIndex, setSelectedIndex] = useState(0);
    const [validImages, setValidImages] = useState(images);

    const openModal = (image: ImageType, index: number) => {
        setSelectedImage(image);
        setSelectedIndex(index);
        setIsModalOpen(true);
    };

    const closeModal = () => {
        setIsModalOpen(false);
        setSelectedImage(null);
    };

    // Handle navigation in modal
    const nextImage = () => {
        setSelectedIndex((prevIndex) => (prevIndex + 1) % validImages.length);
        setSelectedImage(validImages[(selectedIndex + 1) % validImages.length]);
    };

    const prevImage = () => {
        setSelectedIndex((prevIndex) => (prevIndex - 1 + validImages.length) % validImages.length);
        setSelectedImage(validImages[(selectedIndex - 1 + validImages.length) % validImages.length]);
    };

    // Handle broken images by filtering them out
    const handleImageError = (brokenImage: ImageType) => {
        setValidImages((prevImages) => prevImages.filter((img) => img !== brokenImage));
    };

    useEffect(() => {
        const imagesToHide: ImageType[] = []
        const filteredImages = images.filter((img) => !imagesToHide.includes(img));
        setValidImages(filteredImages);
    }, [images]);

    if (validImages.length === 0) return null;

    return (
        <div className="w-full h-full min-h-[200px] max-h-[400px]">
            <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-4 gap-4 pb-4">
                {validImages.map((image: ImageType, index: number) => (
                    <div 
                        key={index} 
                        className="relative aspect-square bg-gray-700 rounded-lg overflow-hidden hover:shadow-lg transition-shadow duration-300"
                    >
                        <img
                            src={image}
                            alt={`Image ${index + 1}`}
                            className="absolute inset-0 w-full h-full object-cover cursor-pointer hover:opacity-90 transition-opacity duration-300"
                            onClick={() => openModal(image, index)}
                            onError={() => handleImageError(image)}
                            loading="lazy"
                        />
                    </div>
                ))}
            </div>

            {selectedImage && (
                <ImageModal
                    imageSrc={selectedImage}
                    isOpen={isModalOpen}
                    onClose={closeModal}
                    onNext={nextImage}
                    onPrev={prevImage}
                />
            )}
        </div>
    );
}