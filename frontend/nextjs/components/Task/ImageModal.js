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
            className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-60 overflow-auto"
            onClick={handleClose}
            onTouchStart={handleTouchStart}
            onTouchEnd={handleTouchEnd}
        >
            <div className="relative m-4 max-w-full">
                <button
                    className="absolute top-0 right-0 p-2 text-white"
                    onClick={onClose}
                >
                    <svg
                        xmlns="http://www.w3.org/2000/svg"
                        fill="none"
                        viewBox="0 0 24 24"
                        strokeWidth={2}
                        stroke="currentColor"
                        className="w-6 h-6"
                    >
                        <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            d="M6 18L18 6M6 6l12 12"
                        />
                    </svg>
                </button>
                <img
                    src={imageSrc}
                    alt="Full view"
                    className="max-h-[80vh] max-w-full object-contain"
                />
                <button onClick={onPrev} className="absolute left-0 p-2 text-white">
                    Prev
                </button>
                <button onClick={onNext} className="absolute right-0 p-2 text-white">
                    Next
                </button>
            </div>
        </div>
    );
}