import Image from "next/image";

const Header = () => {
  return (
    <div className="fixed top-0 left-0 right-0 z-50">
      <div className="absolute inset-0 backdrop-blur-sm bg-gradient-to-b to-transparent"></div>
      <div className="container relative h-[60px] px-4 lg:h-[80px] lg:px-0 pt-4 pb-4">
        <div className="flex justify-center items-center h-full">
          <a href="/">
            <Image
              src="/img/gptr-logo.png"
              alt="logo"
              width={60}
              height={60}
              className="lg:h-16 lg:w-16"
            />
          </a>
        </div>
      </div>
    </div>
  );
};

export default Header;
