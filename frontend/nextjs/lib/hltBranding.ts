export const hltBranding = {
  enabled: process.env.NEXT_PUBLIC_HLT_BRANDING !== "0",
  productName: process.env.NEXT_PUBLIC_HLT_BRAND_NAME || "Mastery Research",
  platformName: process.env.NEXT_PUBLIC_HLT_PLATFORM_NAME || "Katailyst",
  ownerName: process.env.NEXT_PUBLIC_HLT_OWNER_NAME || "HLT",
  subtitle: process.env.NEXT_PUBLIC_HLT_BRAND_SUBTITLE || "",
  heroTitle:
    process.env.NEXT_PUBLIC_HLT_HERO_TITLE || "What should Mastery research?",
  heroNote:
    process.env.NEXT_PUBLIC_HLT_HERO_NOTE ||
    "Choose focused context sources, then generate a cited research report.",
  katailystUrl:
    process.env.NEXT_PUBLIC_KATAILYST_URL || "https://www.katailyst.com",
  uiUrl:
    process.env.NEXT_PUBLIC_GPTR_UI_URL ||
    "https://gpt-researcher-ui.vercel.app",
  icon: process.env.NEXT_PUBLIC_HLT_BRAND_ICON || "/img/katailyst-mark.svg",
  accent: "#155EEF",
  deepNavy: "#0B2B33",
  warmWhite: "#F8FAFB",
};
