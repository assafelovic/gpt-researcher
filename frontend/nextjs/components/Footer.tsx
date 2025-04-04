import React from 'react';
import Image from "next/image";
import Link from "next/link";
import Modal from './Settings/Modal';
import { ChatBoxSettings } from '@/types/data';

interface FooterProps {
  chatBoxSettings: ChatBoxSettings;
  setChatBoxSettings: React.Dispatch<React.SetStateAction<ChatBoxSettings>>;
}

const Footer: React.FC<FooterProps> = ({ chatBoxSettings, setChatBoxSettings }) => {
  // Add domain filtering from URL parameters
  if (typeof window !== 'undefined') {
    const urlParams = new URLSearchParams(window.location.search);
    const urlDomains = urlParams.get("domains");
    if (urlDomains) {
      // Split domains by comma if multiple domains are provided
      const domainArray = urlDomains.split(',').map(domain => ({
        value: domain.trim()
      }));
      localStorage.setItem('domainFilters', JSON.stringify(domainArray));
    }
  }

  return (
    <>
      <div className="container flex flex-col sm:flex-row min-h-[60px] sm:min-h-[72px] mt-2 items-center justify-center sm:justify-between border-t border-gray-700/30 px-4 pb-3 pt-4 sm:py-5 lg:px-0 bg-transparent backdrop-blur-sm gap-3 sm:gap-0">
        <Modal setChatBoxSettings={setChatBoxSettings} chatBoxSettings={chatBoxSettings} />
        <div className="text-xs sm:text-sm text-gray-100 text-center sm:text-left order-2 sm:order-1">
            © {new Date().getFullYear()} GPT Researcher. All rights reserved.
        </div>
        <div className="flex items-center gap-4 order-1 sm:order-2 mb-2 sm:mb-0">
          <Link href={"https://gptr.dev"} target="_blank" className="p-1">
              <svg 
                xmlns="http://www.w3.org/2000/svg" 
                viewBox="0 0 24 24" 
                fill="none" 
                stroke="currentColor" 
                strokeWidth="2" 
                strokeLinecap="round" 
                strokeLinejoin="round" 
                className="w-6 h-6 sm:w-7 sm:h-7 text-white hover:text-teal-400 transition-colors duration-300"
              >
                <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" />
                <polyline points="9 22 9 12 15 12 15 22" />
              </svg>
          </Link>
          <Link href={"https://github.com/assafelovic/gpt-researcher"} target="_blank" className="p-1">
            <img
              src={"/img/github.svg"}
              alt="github"
              width={24}
              height={24}
              className="w-6 h-6 sm:w-7 sm:h-7"
            />{" "}
          </Link>
          <Link href={"https://discord.gg/QgZXvJAccX"} target="_blank" className="p-1">
              <img
                src={"/img/discord.svg"}
                alt="discord"
                width={24}
                height={24}
                className="w-6 h-6 sm:w-7 sm:h-7"
              />{" "}
          </Link>
          <Link href={"https://hub.docker.com/r/gptresearcher/gpt-researcher"} target="_blank" className="p-1">
              <img
                src={"/img/docker.svg"}
                alt="docker"
                width={24}
                height={24}
                className="w-6 h-6 sm:w-7 sm:h-7"
              />{" "}
          </Link>
        </div>
      </div>
    </>
  );
};

export default Footer;