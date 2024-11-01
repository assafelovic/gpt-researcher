import React, { useEffect } from 'react';

export default function ImageModal({ imageSrc, isOpen, onClose, onNext, onPrev }) {
    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 bg-black bg-opacity-75 z-50 flex items-center justify-center p-4">
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