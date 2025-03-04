/**
 * Main entry point for the GPT Researcher UI
 */
import { initDarkMode } from './theme';
import { initSettingsModal, initConfigFileUpload } from './settings';
import { initFileUpload, setupTagInput } from './fileUpload';
import { setupConsoleLogRedirect } from './logging';
import { startResearch } from './research';
import { initChat } from './chat';

/**
 * Toggles the advanced section visibility
 */
function toggleAdvanced(): void {
    const advancedSection = document.getElementById("advancedSection");
    const advancedToggle = document.getElementById("advancedToggle") as HTMLInputElement | null;
    
    if (!advancedSection || !advancedToggle) return;
    
    const isChecked = advancedToggle.checked;
    advancedSection.classList.toggle("visible", isChecked);

    localStorage.setItem("showAdvanced", isChecked ? "true" : "false");
}

/**
 * Initializes the application when the DOM is loaded
 */
document.addEventListener("DOMContentLoaded", function () {
    console.log("DOM loaded, initializing application");

    setupConsoleLogRedirect();

    initDarkMode();

    initSettingsModal();

    initConfigFileUpload();

    initFileUpload();

    setupTagInput("sourceUrlsInput", "sourceUrls");
    setupTagInput("queryDomainsInput", "queryDomains");

    initChat();

    // Set default values from localStorage
    const defaultReportType = localStorage.getItem("defaultReportType");
    const defaultReportFormat = localStorage.getItem("defaultReportFormat");

    if (defaultReportType) {
        const reportTypeSelect = document.getElementById("report_type") as HTMLSelectElement | null;
        if (reportTypeSelect) reportTypeSelect.value = defaultReportType;
    }

    if (defaultReportFormat) {
        const reportFormatSelect = document.getElementById("report_format") as HTMLSelectElement | null;
        if (reportFormatSelect) reportFormatSelect.value = defaultReportFormat;
    }

    // Set up the advanced toggle
    const advancedToggle = document.getElementById("advancedToggle") as HTMLInputElement | null;
    if (advancedToggle) {
        advancedToggle.addEventListener("change", toggleAdvanced);
        
        // Initialize advanced section based on localStorage
        if (localStorage.getItem("showAdvanced") === "true") {
            advancedToggle.checked = true;
            toggleAdvanced();
        }
    }

    // Set up the research form
    const researchForm = document.getElementById("research-form") as HTMLFormElement | null;
    console.log("Research form element:", researchForm);

    if (researchForm) {
        console.log("Research form found, attaching event listener");
        researchForm.addEventListener("submit", startResearch);
    } else {
        console.error(
            "Research form not found! This is likely the cause of the issue."
        );

        const forms = document.getElementsByTagName("form");
        console.log("Available forms:", forms.length);
        for (let i = 0; i < forms.length; i++) {
            console.log(`Form ${i} id:`, forms[i].id);

            forms[i].addEventListener("submit", startResearch);
            console.log(`Attached event listener to form ${i}`);
        }
    }

    // Set up the submit button
    const submitBtn = document.getElementById("submitBtn") as HTMLButtonElement | null;
    if (submitBtn) {
        console.log("Submit button found, attaching direct click event listener");
        submitBtn.addEventListener("click", function (event) {
            event.preventDefault();
            console.log("Submit button clicked directly");

            const form = this.closest("form") as HTMLFormElement | null;
            if (form) {
                console.log("Form found from button, submitting");

                const submitEvent = new Event("submit", {
                    bubbles: true,
                    cancelable: true,
                });
                form.dispatchEvent(submitEvent);
            } else {
                console.error("Could not find form from submit button");

                const targetForm = document.getElementById("research-form") as HTMLFormElement || 
                                                    document.querySelector("form") as HTMLFormElement;
                
                if (targetForm) {
                    startResearch({
                        preventDefault: () => {},
                        target: targetForm
                    } as unknown as Event);
                }
            }
        });
    } else {
        console.error("Submit button not found!");
    }
}); 