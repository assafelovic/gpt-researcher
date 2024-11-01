import React, { useState, useEffect } from 'react';
import ImageModal from './ImageModal'; // Import the ImageModal component

export default function ImagesGrid({ images }) {
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [selectedImage, setSelectedImage] = useState(null);
    const [selectedIndex, setSelectedIndex] = useState(0);
    const [validImages, setValidImages] = useState(images);

    const openModal = (image, index) => {
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
    const handleImageError = (brokenImage) => {
        setValidImages((prevImages) => prevImages.filter((img) => img !== brokenImage));
    };

    useEffect(() => {
        const imagesToHide = []
        const filteredImages = images.filter((img) => !imagesToHide.includes(img));
        setValidImages(filteredImages);
    }, [images]);

    // Hide the entire component if there are no valid images
    if (validImages.length === 0) return null;

    return (
        <div className="w-full mt-5 mb-5">
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
                {validImages.map((image, index) => (
                    <div key={index} className="relative aspect-square">
                        <img
                            src={image}
                            alt={`Image ${index + 1}`}
                            className="absolute inset-0 w-full h-full object-cover rounded-lg cursor-pointer hover:opacity-90 transition-opacity"
                            onClick={() => openModal(image, index)}
                            onError={() => handleImageError(image)}
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