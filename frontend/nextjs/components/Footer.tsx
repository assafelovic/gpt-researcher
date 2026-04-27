import React, { useEffect } from "react";
import { ChatBoxSettings } from "@/types/data";

interface FooterProps {
  chatBoxSettings: ChatBoxSettings;
  setChatBoxSettings: React.Dispatch<React.SetStateAction<ChatBoxSettings>>;
}

const Footer: React.FC<FooterProps> = () => {
  useEffect(() => {
    const urlParams = new URLSearchParams(window.location.search);
    const urlDomains = urlParams.get("domains");
    if (urlDomains) {
      const domainArray = urlDomains.split(",").map((domain) => ({
        value: domain.trim(),
      }));
      localStorage.setItem("domainFilters", JSON.stringify(domainArray));
    }
  }, []);

  return null;
};

export default Footer;
