import React from 'react';

export default function ImageModal({ imageSrc, isOpen, onClose }) {
    if (!isOpen) return null;

    const handleClose = (e) => {
        if (e.target === e.currentTarget) {
            onClose();
        }
    };

    return (
        <div
            className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-60 overflow-auto"
            onClick={handleClose}
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
            </div>
        </div>
    );
}
