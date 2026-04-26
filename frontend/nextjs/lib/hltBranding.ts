export const hltBranding = {
  enabled: process.env.NEXT_PUBLIC_HLT_BRANDING !== "0",
  productName: process.env.NEXT_PUBLIC_HLT_BRAND_NAME || "Mastery Research",
  platformName: process.env.NEXT_PUBLIC_HLT_PLATFORM_NAME || "Katailyst",
  ownerName: process.env.NEXT_PUBLIC_HLT_OWNER_NAME || "HLT",
  subtitle:
    process.env.NEXT_PUBLIC_HLT_BRAND_SUBTITLE || "Katailyst research console",
  heroTitle:
    process.env.NEXT_PUBLIC_HLT_HERO_TITLE ||
    "Research anything with Mastery-grade context.",
  heroNote:
    process.env.NEXT_PUBLIC_HLT_HERO_NOTE ||
    "Source-backed web, codebase, Katailyst registry, and metrics research through GPT Researcher.",
  katailystUrl:
    process.env.NEXT_PUBLIC_KATAILYST_URL || "https://www.katailyst.com",
  uiUrl:
    process.env.NEXT_PUBLIC_GPTR_UI_URL ||
    "https://gpt-researcher-ui.vercel.app",
  icon: process.env.NEXT_PUBLIC_HLT_BRAND_ICON || "/img/hlt-mastery-icon.png",
  accent: "#155EEF",
  deepNavy: "#0B2B33",
  warmWhite: "#F8FAFB",
};
