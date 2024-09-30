import Image from "next/image";
import Link from "next/link";

const Header = () => {
  return (
    <header className="bg-gradient-to-r from-gray-50 to-gray-100 border-b border-gray-200">
      <div className="container mx-auto px-4 py-3 lg:py-4">
        <div className="flex items-center justify-between">
          <Link href="/" className="flex items-center space-x-2">
            <Image
              src="/img/gptr-logo.png"
              alt="GPT Researcher Logo"
              width={40}
              height={40}
              className="w-10 h-10 lg:w-12 lg:h-12 transition-transform hover:scale-105"
            />
            <span className="text-xl lg:text-2xl font-semibold text-gray-800">
              GPT Researcher
            </span>
          </Link>
          <nav>
            <ul className="flex space-x-6">
              <NavItem href="/about">About</NavItem>
              <NavItem href="/docs">Docs</NavItem>
              <NavItem href="/contact">Contact</NavItem>
            </ul>
          </nav>
        </div>
      </div>
    </header>
  );
};

const NavItem = ({ href, children }: { href: string; children: React.ReactNode }) => (
  <li>
    <Link
      href={href}
      className="text-gray-600 hover:text-gray-900 transition-colors duration-200"
    >
      {children}
    </Link>
  </li>
);

export default Header;