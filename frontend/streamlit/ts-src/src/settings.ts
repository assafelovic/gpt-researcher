/**
 * Settings management for the GPT Researcher UI
 */
import { ResearchSettings } from './types';
import { showLoading, hideLoading } from './utils';

/**
 * Initializes the settings modal
 */
export function initSettingsModal(): void {
    const settingsModal = document.getElementById("settingsModal");
    const closeSettings = document.getElementById("closeSettings");
    const saveSettings = document.getElementById("saveSettings");
    
    if (!settingsModal || !closeSettings || !saveSettings) return;
    
    const settingsTabs = document.querySelectorAll<HTMLElement>(".settings-tab");
    const settingsTabContents = document.querySelectorAll<HTMLElement>(".settings-tab-content");

    const container = document.querySelector<HTMLElement>(".container");
    if (!container) return;
    
    container.style.position = "relative";

    const configButtons = document.createElement("div");
    configButtons.className = "config-buttons";
    container.appendChild(configButtons);

    const settingsButton = document.createElement("button");
    settingsButton.className = "config-button";
    settingsButton.innerHTML = "⚙️ API Settings";
    configButtons.appendChild(settingsButton);

    const exportSettingsButton = document.createElement("button");
    exportSettingsButton.className = "config-button";
    exportSettingsButton.innerHTML = "📤 Export Settings";
    configButtons.appendChild(exportSettingsButton);

    const loadConfigButton = document.createElement("button");
    loadConfigButton.className = "config-button";
    loadConfigButton.innerHTML = "📥 Load Config";
    configButtons.appendChild(loadConfigButton);

    exportSettingsButton.addEventListener("click", () => {
        exportSettings();
    });

    settingsButton.addEventListener("click", () => {
        settingsModal.style.display = "flex";
        loadSettings();
    });

    loadConfigButton.addEventListener("click", () => {
        const configFileInput = document.getElementById("configFileInput");
        if (configFileInput) {
            (configFileInput as HTMLInputElement).click();
        }
    });

    closeSettings.addEventListener("click", () => {
        settingsModal.style.display = "none";
    });

    saveSettings.addEventListener("click", () => {
        saveAllSettings();
        settingsModal.style.display = "none";
    });

    settingsTabs.forEach((tab) => {
        tab.addEventListener("click", () => {
            const tabId = tab.getAttribute("data-tab");
            if (!tabId) return;

            settingsTabs.forEach((t) => t.classList.remove("active"));
            tab.classList.add("active");

            settingsTabContents.forEach((content) => {
                content.style.display = "none";
            });
            
            const tabContent = document.getElementById(`${tabId}Tab`);
            if (tabContent) {
                tabContent.style.display = "block";
            }
        });
    });
}

/**
 * Loads settings from localStorage
 */
function loadSettings(): void {
    const apiKey = document.getElementById("apiKey") as HTMLInputElement | null;

    if (apiKey) {
        apiKey.value = localStorage.getItem("apiKey") || "";
    }
}

/**
 * Saves all settings to localStorage
 */
function saveAllSettings(): void {
    const apiKey = document.getElementById("apiKey") as HTMLInputElement | null;

    if (apiKey) {
        localStorage.setItem("apiKey", apiKey.value);
    }
}

/**
 * Collects all settings from the research form
 * @returns The collected settings
 */
export function collectAllSettings(): ResearchSettings {
    const settings: ResearchSettings = {};
    const form = document.getElementById("researchForm") as HTMLFormElement | null;
    
    if (!form) return settings;

    const inputs = form.querySelectorAll<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>("input, select, textarea");

    inputs.forEach((input) => {
        let value: string | number | boolean;

        if (input.type === "checkbox") {
            value = (input as HTMLInputElement).checked;
        } else if (input.type === "number") {
            value = parseFloat(input.value);
        } else {
            value = input.value;
        }

        if (input.name) {
            settings[input.name] = value;
        }
    });

    return settings;
}

/**
 * Exports settings to a JSON file
 */
export function exportSettings(): void {
    const settings = collectAllSettings();
    const jsonSettings = JSON.stringify(settings, null, 2);

    const blob = new Blob([jsonSettings], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "gpt_researcher_config.json";
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

/**
 * Loads configuration from a JSON string
 * @param jsonData The JSON data to load
 */
export async function loadConfigFromJSON(jsonData: string): Promise<void> {
    showLoading("Loading configuration...");

    try {
        const response = await fetch("/load_config", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: jsonData,
        });

        const result = await response.json();

        if (response.ok) {
            window.location.reload();
        } else {
            alert(`Error loading configuration: ${result.message}`);
        }
    } catch (error) {
        if (error instanceof Error) {
            alert(`Error: ${error.message}`);
        } else {
            alert(`An unknown error occurred`);
        }
    } finally {
        hideLoading();
    }
}

/**
 * Initializes the config file upload functionality
 */
export function initConfigFileUpload(): void {
    const configFileInput = document.createElement("input");
    configFileInput.type = "file";
    configFileInput.id = "configFileInput";
    configFileInput.accept = ".json";
    configFileInput.style.display = "none";
    document.body.appendChild(configFileInput);

    configFileInput.addEventListener("change", (event) => {
        const target = event.target as HTMLInputElement;
        const file = target.files?.[0];
        if (file) {
            const reader = new FileReader();
            reader.onload = (e) => {
                const result = e.target?.result;
                if (typeof result === 'string') {
                    loadConfigFromJSON(result);
                }
            };
            reader.readAsText(file);
        }
    });
} 