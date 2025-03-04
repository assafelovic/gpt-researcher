/**
 * Theme management for the GPT Researcher UI
 */

type Theme = 'light' | 'dark' | 'system';

/**
 * Initializes dark mode functionality
 */
export function initDarkMode(): void {
    const themeToggle = document.getElementById("themeToggle");
    if (!themeToggle) return;
    
    const sunIcon = themeToggle.querySelector(".sun-icon") as HTMLElement;
    const moonIcon = themeToggle.querySelector(".moon-icon") as HTMLElement;
    const themeSelect = document.getElementById("themeSelect") as HTMLSelectElement | null;

    const savedTheme = localStorage.getItem("theme") as Theme | null;
    const prefersDark =
        window.matchMedia &&
        window.matchMedia("(prefers-color-scheme: dark)").matches;

    if (
        savedTheme === "dark" ||
        (savedTheme === "system" && prefersDark) ||
        (!savedTheme && prefersDark)
    ) {
        document.documentElement.classList.add("dark-mode");
        if (sunIcon) sunIcon.style.display = "none";
        if (moonIcon) moonIcon.style.display = "block";
        if (themeSelect) themeSelect.value = savedTheme || "system";
    } else {
        document.documentElement.classList.remove("dark-mode");
        if (sunIcon) sunIcon.style.display = "block";
        if (moonIcon) moonIcon.style.display = "none";
        if (themeSelect) themeSelect.value = savedTheme || "light";
    }

    themeToggle.addEventListener("click", () => {
        const isDark = document.documentElement.classList.toggle("dark-mode");
        if (sunIcon) sunIcon.style.display = isDark ? "none" : "block";
        if (moonIcon) moonIcon.style.display = isDark ? "block" : "none";
        localStorage.setItem("theme", isDark ? "dark" : "light");
        if (themeSelect) themeSelect.value = isDark ? "dark" : "light";
    });

    window
        .matchMedia("(prefers-color-scheme: dark)")
        .addEventListener("change", (e) => {
            if (localStorage.getItem("theme") === "system") {
                const shouldBeDark = e.matches;
                document.documentElement.classList.toggle("dark-mode", shouldBeDark);
                if (sunIcon) sunIcon.style.display = shouldBeDark ? "none" : "block";
                if (moonIcon) moonIcon.style.display = shouldBeDark ? "block" : "none";
            }
        });

    if (themeSelect) {
        themeSelect.addEventListener("change", () => {
            const selectedTheme = themeSelect.value as Theme;
            localStorage.setItem("theme", selectedTheme);

            const prefersDark =
                window.matchMedia &&
                window.matchMedia("(prefers-color-scheme: dark)").matches;
            const shouldBeDark =
                selectedTheme === "dark" || (selectedTheme === "system" && prefersDark);

            document.documentElement.classList.toggle("dark-mode", shouldBeDark);
            if (sunIcon) sunIcon.style.display = shouldBeDark ? "none" : "block";
            if (moonIcon) moonIcon.style.display = shouldBeDark ? "block" : "none";
        });
    }
} 