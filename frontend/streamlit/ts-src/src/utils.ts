/**
 * Utility functions for the GPT Researcher UI
 */

/**
 * Shows a loading message in the console
 * @param message The message to display
 */
export function showLoading(message: string = "Processing your request..."): void {
    console.log("Loading status: " + message);
}

/**
 * Hides the loading indicator
 */
export function hideLoading(): void {
    // Implementation can be added later if needed
}

/**
 * Downloads content as a file
 * @param content The content to download
 * @param filename The name of the file
 * @param contentType The content type of the file
 */
export function downloadAsFile(content: string, filename: string, contentType: string): void {
    const blob = new Blob([content], { type: contentType });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

/**
 * Gets an icon for a file format
 * @param format The file format
 * @returns An emoji icon representing the format
 */
export function getFormatIcon(format: string): string {
    switch (format.toLowerCase()) {
        case "pdf":
            return "📄";
        case "docx":
            return "📝";
        case "md":
            return "📋";
        default:
            return "📄";
    }
} 