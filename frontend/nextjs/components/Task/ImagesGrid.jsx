import React, { useState, useEffect } from 'react';
import ImageModal from './ImageModal';

const ImagesGrid = () => {
    const [validImages, setValidImages] = useState([]);
    const [selectedImage, setSelectedImage] = useState(null);
    const [isModalOpen, setIsModalOpen] = useState(false);

    useEffect(() => {
        // Fetch valid images from the backend
        fetchValidImages();
    }, []);

    const fetchValidImages = async () => {
        try {
            const response = await fetch('/api/images');
            const data = await response.json();
            setValidImages(data);
        } catch (error) {
            console.error('Error fetching valid images:', error);
        }
    };

    const openModal = (image, index) => {
        setSelectedImage(image);
        setIsModalOpen(true);
    };

    const closeModal = () => {
        setSelectedImage(null);
        setIsModalOpen(false);
    };

    const nextImage = () => {
        const currentIndex = validImages.indexOf(selectedImage);
        const nextIndex = (currentIndex + 1) % validImages.length;
        setSelectedImage(validImages[nextIndex]);
    };

    const prevImage = () => {
        const currentIndex = validImages.indexOf(selectedImage);
        const prevIndex = (currentIndex - 1 + validImages.length) % validImages.length;
        setSelectedImage(validImages[prevIndex]);
    };

    const handleImageError = (image) => {
        console.error(`Error loading image: ${image}`);
    };

    return (
        <div className="w-full mt-5 mb-5">
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
                {validImages.map((image, index) => (
                    <div 
                        key={index} 
                        className="relative pt-[100%]" // Creates a square aspect ratio container
                    >
                        <img
                            src={image}
                            alt={`Image ${index + 1}`}
                            className="absolute top-0 left-0 w-full h-full object-contain bg-gray-100 rounded-lg cursor-pointer hover:opacity-90 transition-opacity"
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
                    className="max-h-[80vh] w-auto" // Constrain modal image height
                />
            )}
        </div>
    );
};

export default ImagesGrid; 