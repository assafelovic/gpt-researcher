// /frontend/nextjs/public/embed.js
(function() {
    window.GPTResearcher = {
        init: function() {
            // Create container
            const container = document.createElement('div');
            container.id = 'gpt-researcher-container';
            container.style.width = '100%';
            container.style.height = '100vh';
            container.style.overflow = 'hidden'; // Hide scrollbar

            // Create iframe
            const iframe = document.createElement('iframe');
            iframe.src = 'https://gptr.app';
            iframe.style.width = '100%';
            iframe.style.border = 'none';
            iframe.style.height = '100%'; // Set to 100% instead of window.innerHeight
            iframe.style.overflow = 'hidden'; // Hide scrollbar

            // Add custom styles to hide scrollbars
            const style = document.createElement('style');
            style.textContent = `
                #gpt-researcher-container {
                    -ms-overflow-style: none;  /* IE and Edge */
                    scrollbar-width: none;     /* Firefox */
                }
                #gpt-researcher-container::-webkit-scrollbar {
                    display: none;             /* Chrome, Safari and Opera */
                }
                #gpt-researcher-container iframe {
                    -ms-overflow-style: none;
                    scrollbar-width: none;
                }
                #gpt-researcher-container iframe::-webkit-scrollbar {
                    display: none;
                }
            `;
            document.head.appendChild(style);

            // Add iframe to container
            container.appendChild(iframe);

            // Add container to document
            document.currentScript.parentNode.insertBefore(container, document.currentScript);

            // Handle resize
            window.addEventListener('resize', () => {
                iframe.style.height = '100%';
            });

            // Ensure height is set after iframe loads
            iframe.addEventListener('load', () => {
                iframe.style.height = '100%';
            });
        },

        configure: function(options = {}) {
            if (options.height) {
                const iframe = document.querySelector('#gpt-researcher-container iframe');
                if (iframe) {
                    iframe.style.height = options.height + 'px';
                }
            }
        }
    };

    // Initialize when script loads
    window.GPTResearcher.init();
})();