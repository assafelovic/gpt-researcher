import React, { useEffect } from 'react';

export default function ImageModal({ imageSrc, isOpen, onClose, onNext, onPrev }) {
    if (!isOpen) return null;

    // Set up keyboard event listeners
    useEffect(() => {
        const handleKeyDown = (e) => {
            if (e.key === 'ArrowLeft') {
                onPrev();
            } else if (e.key === 'ArrowRight') {
                onNext();
            } else if (e.key === 'Escape') {
                onClose();
            }
        };

        document.addEventListener('keydown', handleKeyDown);
        return () => document.removeEventListener('keydown', handleKeyDown);
    }, [onClose, onNext, onPrev]);

    // Swipe detection for mobile
    let touchStartX = 0;
    let touchEndX = 0;

    const handleTouchStart = (e) => {
        touchStartX = e.changedTouches[0].screenX;
    };

    const handleTouchEnd = (e) => {
        touchEndX = e.changedTouches[0].screenX;
        handleSwipeGesture();
    };

    const handleSwipeGesture = () => {
        if (touchEndX < touchStartX - 50) {
            onNext();
        } else if (touchEndX > touchStartX + 50) {
            onPrev();
        }
    };

    const handleClose = (e) => {
        if (e.target === e.currentTarget) {
            onClose();
        }
    };

    return (
        <div
            className="fixed inset-0 bg-black bg-opacity-75 z-50 flex items-center justify-center p-4 overflow-auto"
            onClick={handleClose}
            onTouchStart={handleTouchStart}
            onTouchEnd={handleTouchEnd}
        >
            <div className="relative max-w-[90vw] max-h-[90vh] flex items-center justify-center">
                <button
                    onClick={onPrev}
                    className="absolute left-4 z-10 bg-black bg-opacity-50 text-white p-2 rounded-full hover:bg-opacity-75"
                >
                    ←
                </button>
                <img
                    src={imageSrc}
                    alt="Modal view"
                    className="max-h-[90vh] max-w-[90vw] object-contain"
                />
                <button
                    onClick={onNext}
                    className="absolute right-4 z-10 bg-black bg-opacity-50 text-white p-2 rounded-full hover:bg-opacity-75"
                >
                    →
                </button>
                <button
                    onClick={onClose}
                    className="absolute top-4 right-4 z-10 bg-black bg-opacity-50 text-white p-2 rounded-full hover:bg-opacity-75"
                >
                    ×
                </button>
            </div>
        </div>
    );
}
