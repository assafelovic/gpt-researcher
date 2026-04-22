export const hltBranding = {
  enabled: process.env.NEXT_PUBLIC_HLT_BRANDING !== "0",
  productName: process.env.NEXT_PUBLIC_HLT_BRAND_NAME || "Katailyst Research",
  platformName: process.env.NEXT_PUBLIC_HLT_PLATFORM_NAME || "Katailyst",
  ownerName: process.env.NEXT_PUBLIC_HLT_OWNER_NAME || "HLT",
  subtitle: process.env.NEXT_PUBLIC_HLT_BRAND_SUBTITLE || "Research workspace",
  heroTitle: process.env.NEXT_PUBLIC_HLT_HERO_TITLE || "What should Catalyst research next?",
  heroNote:
    process.env.NEXT_PUBLIC_HLT_HERO_NOTE ||
    "Built on GPT Researcher for source-backed web and local research.",
  katailystUrl: process.env.NEXT_PUBLIC_KATAILYST_URL || "https://www.katailyst.com",
  uiUrl: process.env.NEXT_PUBLIC_GPTR_UI_URL || "https://gpt-researcher-ui.vercel.app",
  accent: "#155EEF",
  deepNavy: "#0B2B33",
  warmWhite: "#F8FAFB",
};
