import Image from "next/image";
import Link from "next/link";
import Modal from './Settings/Modal';

const Footer = ({ setChatBoxSettings, chatBoxSettings }) => {
  return (
    <footer className="bg-gradient-to-r from-gray-50 to-gray-100 border-t border-gray-200">
      <div className="container mx-auto px-4 py-6 flex items-center justify-between">
        <Modal setChatBoxSettings={setChatBoxSettings} chatBoxSettings={chatBoxSettings} />
        
        <div className="text-sm text-gray-500 font-light">
          © {new Date().getFullYear()} GPT Researcher. All rights reserved.
        </div>
        
        <div className="flex items-center space-x-4">
          <SocialLink href="https://github.com/assafelovic/gpt-researcher" icon="/img/github.svg" alt="GitHub" />
          <SocialLink href="https://discord.gg/QgZXvJAccX" icon="/img/discord.svg" alt="Discord" />
          <SocialLink href="https://hub.docker.com/r/gptresearcher/gpt-researcher" icon="/img/docker.svg" alt="Docker" />
        </div>
      </div>
    </footer>
  );
};

const SocialLink = ({ href, icon, alt }) => (
  <Link href={href} target="_blank" className="transition-transform hover:scale-110">
    <Image src={icon} alt={alt} width={24} height={24} className="opacity-70 hover:opacity-100" />
  </Link>
);

export default Footer;