import React, { useState, useEffect } from 'react';
import ImageModal from './ImageModal'; // Import the ImageModal component

export default function ImagesCarousel({ images }) {
    const [activeIndex, setActiveIndex] = useState(0);
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [selectedImage, setSelectedImage] = useState(null);
    const [validImages, setValidImages] = useState(images); // Keep track of valid images

    const nextSlide = () => {
        setActiveIndex((prevIndex) => (prevIndex + 1) % validImages.length);
    };

    const prevSlide = () => {
        setActiveIndex((prevIndex) => (prevIndex - 1 + validImages.length) % validImages.length);
    };

    const openModal = (image) => {
        setSelectedImage(image);
        setIsModalOpen(true);
    };

    const closeModal = () => {
        setIsModalOpen(false);
        setSelectedImage(null);
    };

    // Handle broken images by filtering them out
    const handleImageError = (brokenImage) => {
        setValidImages((prevImages) => prevImages.filter((img) => img !== brokenImage));
    };

    useEffect(() => {
        const imagesToHide = ['https://gptr.dev/_ipx/w_3840,q_75/%2F_next%2Fstatic%2Fmedia%2Fbg-pattern.5aa07776.webp?url=%2F_next%2Fstatic%2Fmedia%2Fbg-pattern.5aa07776.webp&w=3840&q=75',"https://tavily.com/_ipx/w_3840,q_75/%2F_next%2Fstatic%2Fmedia%2Fbg-pattern.5aa07776.webp?url=%2F_next%2Fstatic%2Fmedia%2Fbg-pattern.5aa07776.webp&w=3840&q=75"]
        const filteredImages = images.filter((img) => !imagesToHide.includes(img));
        setValidImages(filteredImages);
    }, [images]);

    // Hide the entire component if there are no valid images
    if (validImages.length === 0) return null;

    return (
        <div id="default-carousel" className="relative w-full" data-carousel="slide">
            <div className="relative h-56 overflow-hidden rounded-lg md:h-96">
                {validImages.map((image, index) => (
                    <div
                        key={index}
                        className={`duration-700 ease-in-out ${index === activeIndex ? '' : 'hidden'}`}
                        data-carousel-item
                    >
                        <img
                            src={image}
                            className="absolute block w-full -translate-x-1/2 -translate-y-1/2 top-1/2 left-1/2 cursor-pointer"
                            alt={`Slide ${index + 1}`}
                            onClick={() => openModal(image)} // Open modal on image click
                            onError={() => handleImageError(image)} // Handle broken images
                        />
                    </div>
                ))}
            </div>

            {/* Only show indicators and buttons if there is more than 1 valid image */}
            {validImages.length > 1 && (
                <>
                    <div className="absolute z-30 flex -translate-x-1/2 bottom-5 left-1/2 space-x-3 rtl:space-x-reverse">
                        {validImages.map((_, index) => (
                            <button
                                key={index}
                                type="button"
                                className={`w-3 h-3 rounded-full ${index === activeIndex ? 'bg-gray-800' : 'bg-gray-400'}`}
                                aria-current={index === activeIndex ? 'true' : 'false'}
                                aria-label={`Slide ${index + 1}`}
                                onClick={() => setActiveIndex(index)}
                                data-carousel-slide-to={index}
                            ></button>
                        ))}
                    </div>

                    <button
                        type="button"
                        className="absolute top-0 start-0 z-30 flex items-center justify-center h-full px-4 cursor-pointer group focus:outline-none"
                        onClick={prevSlide}
                        data-carousel-prev
                    >
                        <span className="inline-flex items-center justify-center w-10 h-10 rounded-full bg-white/30 dark:bg-gray-800/30 group-hover:bg-white/50 dark:group-hover:bg-gray-800/60 group-focus:ring-4 group-focus:ring-white dark:group-focus:ring-gray-800/70 group-focus:outline-none">
                            <svg
                                className="w-4 h-4 text-white dark:text-gray-800 rtl:rotate-180"
                                xmlns="http://www.w3.org/2000/svg"
                                fill="none"
                                viewBox="0 0 6 10"
                            >
                                <path
                                    stroke="currentColor"
                                    strokeLinecap="round"
                                    strokeLinejoin="round"
                                    strokeWidth="2"
                                    d="M5 1 1 5l4 4"
                                />
                            </svg>
                            <span className="sr-only">Previous</span>
                        </span>
                    </button>
                    <button
                        type="button"
                        className="absolute top-0 end-0 z-30 flex items-center justify-center h-full px-4 cursor-pointer group focus:outline-none"
                        onClick={nextSlide}
                        data-carousel-next
                    >
                        <span className="inline-flex items-center justify-center w-10 h-10 rounded-full bg-white/30 dark:bg-gray-800/30 group-hover:bg-white/50 dark:group-hover:bg-gray-800/60 group-focus:ring-4 group-focus:ring-white dark:group-focus:ring-gray-800/70 group-focus:outline-none">
                            <svg
                                className="w-4 h-4 text-white dark:text-gray-800 rtl:rotate-180"
                                xmlns="http://www.w3.org/2000/svg"
                                fill="none"
                                viewBox="0 0 6 10"
                            >
                                <path
                                    stroke="currentColor"
                                    strokeLinecap="round"
                                    strokeLinejoin="round"
                                    strokeWidth="2"
                                    d="m1 9 4-4-4-4"
                                />
                            </svg>
                            <span className="sr-only">Next</span>
                        </span>
                    </button>
                </>
            )}

            {/* Render the modal when it's open */}
            {selectedImage && (
                <ImageModal imageSrc={selectedImage} isOpen={isModalOpen} onClose={closeModal} />
            )}
        </div>
    );
}
