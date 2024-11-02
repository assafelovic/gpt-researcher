import Image from "next/image";

interface HeaderProps {
  loading?: boolean;      // Indicates if research is currently in progress
  isStopped?: boolean;    // Indicates if research was manually stopped
  showResult?: boolean;   // Controls if research results are being displayed
  onStop?: () => void;    // Handler for stopping ongoing research
  onNewResearch?: () => void;  // Handler for starting fresh research
}

const Header = ({ loading, isStopped, showResult, onStop, onNewResearch }: HeaderProps) => {
  return (
    <div className="fixed top-0 left-0 right-0 z-50">
      {/* Original gradient background with blur effect */}
      <div className="absolute inset-0 backdrop-blur-sm bg-gradient-to-b to-transparent"></div>
      
      {/* Header container */}
      <div className="container relative h-[60px] px-4 lg:h-[80px] lg:px-0 pt-4 pb-4">
        <div className="flex flex-col items-center">
          {/* Logo/Home link */}
          <a href="/">
            <Image
              src="/img/gptr-logo.png"
              alt="logo"
              width={60}
              height={60}
              className="lg:h-16 lg:w-16"
            />
          </a>
          
          {/* Action buttons container */}
          <div className="flex gap-2 mt-2 transition-all duration-300 ease-in-out">
            {/* Stop button - shown only during active research */}
            {loading && !isStopped && (
              <button
                onClick={onStop}
                className="flex items-center justify-center px-6 h-8 text-sm text-white bg-red-500 rounded-full hover:bg-red-600 transform hover:scale-105 transition-all duration-200 shadow-lg whitespace-nowrap"
              >
                Stop
              </button>
            )}
            {/* New Research button - shown after stopping or completing research */}
            {(isStopped || !loading) && showResult && (
              <button
                onClick={onNewResearch}
                className="flex items-center justify-center px-6 h-8 text-sm text-white bg-[rgb(168,85,247)] rounded-full hover:bg-[rgb(147,51,234)] transform hover:scale-105 transition-all duration-200 shadow-lg whitespace-nowrap"
              >
                New Research
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Header;
