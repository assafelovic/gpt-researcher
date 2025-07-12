import React, { useEffect } from 'react';
import { TouchEventHandler } from 'react';

interface ImageModalProps {
    imageSrc: any;
    isOpen: boolean;
    onClose: () => void;
    onNext?: () => void;
    onPrev?: () => void;
  }


export default function ImageModal({ imageSrc, isOpen, onClose, onNext, onPrev }: ImageModalProps) {
    useEffect(() => {
        if (!isOpen) return;
        
        const handleKeyDown = (e: KeyboardEvent) => {
            if (e.key === 'ArrowLeft') {
                onPrev?.();
            } else if (e.key === 'ArrowRight') {
                onNext?.();
            } else if (e.key === 'Escape') {
                onClose();
            }
        };

        document.addEventListener('keydown', handleKeyDown);
        return () => document.removeEventListener('keydown', handleKeyDown);
    }, [isOpen, onClose, onNext, onPrev]);

    if (!isOpen) return null;

    // Swipe detection for mobile
    let touchStartX = 0;
    let touchEndX = 0;

    const handleTouchStart = (e: TouchEvent) => {
        touchStartX = e.changedTouches[0].screenX;
    };

    const handleTouchEnd = (e: TouchEvent) => {
        touchEndX = e.changedTouches[0].screenX;
        handleSwipeGesture();
    };

    const handleSwipeGesture = () => {
        if (touchEndX < touchStartX - 50) {
            onNext?.();
        } else if (touchEndX > touchStartX + 50) {
            onPrev?.();
        }
    };

    const handleClose = (e: React.MouseEvent<HTMLDivElement>) => {
        if (e.target === e.currentTarget) {
            onClose();
        }
    };

    return (
        <div
            className="fixed inset-0 bg-black bg-opacity-75 z-50 flex items-center justify-center p-4 overflow-auto"
            onClick={handleClose}
            onTouchStart={handleTouchStart as unknown as TouchEventHandler<HTMLDivElement>}
            onTouchEnd={handleTouchEnd as unknown as TouchEventHandler<HTMLDivElement>}
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
