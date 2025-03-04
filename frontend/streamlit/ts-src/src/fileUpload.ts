/**
 * File upload functionality for the GPT Researcher UI
 */

/**
 * Initializes the file upload area with drag and drop functionality
 */
export function initFileUpload(): void {
    const fileUploadArea = document.getElementById("fileUploadArea");
    const fileInput = document.getElementById("documents") as HTMLInputElement | null;
    const selectedFiles = document.getElementById("selectedFiles");

    if (!fileUploadArea || !fileInput || !selectedFiles) return;

    fileInput.addEventListener("change", () => {
        updateSelectedFiles();
    });

    fileUploadArea.addEventListener("dragover", (e) => {
        e.preventDefault();
        fileUploadArea.classList.add("drag-active");
    });

    fileUploadArea.addEventListener("dragleave", () => {
        fileUploadArea.classList.remove("drag-active");
    });

    fileUploadArea.addEventListener("drop", (e) => {
        e.preventDefault();
        fileUploadArea.classList.remove("drag-active");

        if (e.dataTransfer?.files && e.dataTransfer.files.length > 0) {
            fileInput.files = e.dataTransfer.files;
            updateSelectedFiles();
        }
    });

    fileUploadArea.addEventListener("click", () => {
        fileInput.click();
    });

    /**
     * Updates the selected files display
     */
    function updateSelectedFiles(): void {
        selectedFiles!.innerHTML = "";

        if (fileInput && fileInput.files && fileInput.files.length > 0) {
            const fileList = document.createElement("ul");
            fileList.className = "file-list";

            Array.from(fileInput.files).forEach((file) => {
                const li = document.createElement("li");
                li.textContent = file.name;
                fileList.appendChild(li);
            });

            selectedFiles!.appendChild(fileList);
        }
    }
}

/**
 * Sets up tag input functionality
 * @param containerId The ID of the container element
 * @param hiddenInputId The ID of the hidden input element
 */
export function setupTagInput(containerId: string, hiddenInputId: string): void {
    const container = document.getElementById(containerId);
    if (!container) return;

    const input = container.querySelector("input") as HTMLInputElement | null;
    const hiddenInput = document.getElementById(hiddenInputId) as HTMLInputElement | null;
    
    if (!input || !hiddenInput) return;
    
    const tags = new Set<string>();

    /**
     * Updates the hidden input value with the current tags
     */
    function updateHiddenInput(): void {
        hiddenInput!.value = Array.from(tags).join(",");
    }

    /**
     * Adds a new tag
     * @param value The tag value to add
     */
    function addTag(value: string): void {
        if (!value) return;
        tags.add(value);
        const tag = document.createElement("div");
        tag.className = "tag";
        tag.innerHTML = `
            ${value}
            <span class="tag-remove">×</span>
        `;
        
        const removeButton = tag.querySelector(".tag-remove");
        if (removeButton) {
            removeButton.addEventListener("click", () => {
                tags.delete(value);
                tag.remove();
                updateHiddenInput();
            });
        }
        
        container!.insertBefore(tag, input);
        input!.value = "";
        updateHiddenInput();
    }

    input.addEventListener("keydown", (e) => {
        if (e.key === "Enter" || e.key === ",") {
            e.preventDefault();
            addTag(input.value.trim());
        }
    });

    input.addEventListener("blur", () => {
        if (input.value.trim()) {
            addTag(input.value.trim());
        }
    });
} 