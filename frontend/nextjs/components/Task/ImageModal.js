import React, { useState } from 'react';

function ImageModal({ imageSrc, isOpen, onClose }) {
    if (!isOpen) return null;

    const handleOutsideClick = (e) => {
        if (e.target.id === 'modal-backdrop') {
            onClose();
        }
    };

    return (
        <div
            id="modal-backdrop"
            className="fixed inset-0 z-[999] grid h-screen w-screen place-items-center bg-black bg-opacity-60 backdrop-blur-sm"
            onClick={handleOutsideClick}
        >
            <div className="relative w-3/4 max-w-[75%] rounded-lg bg-white shadow-2xl">
                <div className="relative p-4">
                    <img
                        src={imageSrc}
                        alt="Full Screen"
                        className="w-full object-cover object-center"
                    />
                </div>
            </div>
        </div>
    );
}

export default ImageModal;