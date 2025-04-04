import Image from "next/image";
import React, { FC, useEffect, useState, useRef } from "react";
import InputArea from "./ResearchBlocks/elements/InputArea";
import { motion, AnimatePresence } from "framer-motion";

type THeroProps = {
  promptValue: string;
  setPromptValue: React.Dispatch<React.SetStateAction<string>>;
  handleDisplayResult: (query : string) => void;
};

const Hero: FC<THeroProps> = ({
  promptValue,
  setPromptValue,
  handleDisplayResult,
}) => {
  const [isVisible, setIsVisible] = useState(false);
  const [showGradient, setShowGradient] = useState(true);
  const particlesContainerRef = useRef<HTMLDivElement>(null);
  
  useEffect(() => {
    setIsVisible(true);
    
    // Create particles for the background effect
    if (particlesContainerRef.current) {
      const container = particlesContainerRef.current;
      const particleCount = window.innerWidth < 768 ? 15 : 30; // Reduce particles on mobile
      
      // Clear any existing particles
      container.innerHTML = '';
      
      for (let i = 0; i < particleCount; i++) {
        const particle = document.createElement('div');
        
        // Random particle attributes
        const size = Math.random() * 4 + 1;
        const posX = Math.random() * 100;
        const posY = Math.random() * 100;
        const duration = Math.random() * 50 + 20;
        const delay = Math.random() * 5;
        const opacity = Math.random() * 0.3 + 0.1;
        
        // Apply styles
        particle.className = 'absolute rounded-full bg-white';
        Object.assign(particle.style, {
          width: `${size}px`,
          height: `${size}px`,
          left: `${posX}%`,
          top: `${posY}%`,
          opacity: opacity.toString(),
          animation: `float ${duration}s ease-in-out ${delay}s infinite`,
        });
        
        container.appendChild(particle);
      }
    }
    
    // Add scroll event listener to show/hide gradient
    let lastScrollY = window.scrollY;
    const threshold = 100; // Amount of scroll before hiding gradient
    
    const handleScroll = () => {
      const currentScrollY = window.scrollY;
      
      if (currentScrollY <= threshold) {
        // At or near the top, show gradient
        setShowGradient(true);
      } else if (currentScrollY > lastScrollY) {
        // Scrolling down, hide gradient
        setShowGradient(false);
      } else if (currentScrollY < lastScrollY) {
        // Scrolling up, show gradient
        setShowGradient(true);
      }
      
      lastScrollY = currentScrollY;
    };
    
    window.addEventListener('scroll', handleScroll);
    
    // Clean up function
    return () => {
      if (particlesContainerRef.current) {
        particlesContainerRef.current.innerHTML = '';
      }
      window.removeEventListener('scroll', handleScroll);
    };
  }, []);

  const handleClickSuggestion = (value: string) => {
    setPromptValue(value);
  };

  // Animation variants for consistent animations
  const fadeInUp = {
    hidden: { opacity: 0, y: 20 },
    visible: { opacity: 1, y: 0 }
  };

  return (
    <div className="relative overflow-visible min-h-[80vh] sm:min-h-[85vh] flex items-center pt-[60px] sm:pt-[80px] mt-[-60px] sm:mt-[-130px]">
      {/* Particle background */}
      <div ref={particlesContainerRef} className="absolute inset-0 -z-20"></div>
      
      <motion.div 
        initial="hidden"
        animate={isVisible ? "visible" : "hidden"}
        variants={fadeInUp}
        transition={{ duration: 0.8 }}
        className="flex flex-col items-center justify-center w-full py-6 sm:py-8 md:py-16 lg:pt-10 lg:pb-20"
      >
        <motion.div 
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: isVisible ? 1 : 0, scale: isVisible ? 1 : 0.95 }}
          transition={{ duration: 0.8, delay: 0.2 }}
          className="landing flex flex-col items-center mb-4 sm:mb-6 md:mb-8"
        >
          <motion.h1 
            className="text-3xl xs:text-4xl sm:text-5xl font-black text-center lg:text-7xl mb-1 sm:mb-2 tracking-tight"
            variants={fadeInUp}
            transition={{ duration: 0.8, delay: 0.4 }}
          >
            <div className="mb-2 xs:mb-3 sm:mb-1 md:mb-0">Say Goodbye to</div>
            <span
              style={{
                backgroundImage: 'linear-gradient(to right, #0cdbb6, #1fd0f0, #06dbee)',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
                display: 'block',
                lineHeight: '1.2',
                paddingBottom: '0.1em'
              }}
            >
              Hours of Research
            </span>
          </motion.h1>
          <motion.h2 
            className="text-base sm:text-xl font-light text-center px-4 mb-6 text-gray-300 max-w-2xl"
            variants={fadeInUp}
            transition={{ duration: 0.8, delay: 0.6 }}
          >
            Say Hello to GPT Researcher, your AI partner for instant insights and comprehensive research
          </motion.h2>
          
          {/* Powered by badge */}
          {/*<motion.div
            variants={fadeInUp}
            transition={{ duration: 0.8, delay: 0.7 }}
            className="flex items-center justify-center gap-2 py-2 px-4 rounded-full bg-black/30 backdrop-blur-sm border border-teal-500/20 hover:border-teal-500/40 transition-all duration-300 shadow-sm hover:shadow-teal-900/20"
          >
            <div className="h-1.5 w-1.5 rounded-full bg-teal-400 animate-pulse mr-0.5"></div>
            <span className="text-gray-400 text-sm font-medium">Powered by</span>
            <a 
              href="https://gptr.dev" 
              target="_blank" 
              rel="noopener noreferrer" 
              className="text-white text-[15px] font-bold hover:underline"
            >
              GPT Researcher
            </a>
          </motion.div>*/}
        </motion.div>

        {/* Input section with enhanced styling */}
        <motion.div 
          variants={fadeInUp}
          transition={{ duration: 0.8, delay: 0.8 }}
          className="w-full max-w-[760px] pb-6 sm:pb-8 md:pb-10 px-4 mt-4"
        >
          <div className="relative group">
            <div className="absolute -inset-1 bg-gradient-to-r from-teal-600 via-cyan-500 to-blue-600 rounded-lg blur-md opacity-75 group-hover:opacity-100 transition duration-1000 group-hover:duration-200 animate-gradient-x"></div>
            <div className="relative bg-black bg-opacity-20 backdrop-blur-sm rounded-lg ring-1 ring-gray-800/60">
              <InputArea
                promptValue={promptValue}
                setPromptValue={setPromptValue}
                handleSubmit={handleDisplayResult}
              />
            </div>
          </div>
        </motion.div>

        {/* Suggestions section with enhanced styling */}
        <motion.div 
          variants={fadeInUp}
          transition={{ duration: 0.8, delay: 1 }}
          className="flex flex-wrap items-center justify-center gap-2 xs:gap-3 md:gap-4 pb-6 sm:pb-8 md:pb-10 px-4 lg:flex-nowrap lg:justify-normal"
        >
          <AnimatePresence>
            {suggestions.map((item, index) => (
              <motion.div
                key={item.id}
                variants={fadeInUp}
                initial="hidden"
                animate="visible"
                transition={{ duration: 0.4, delay: 1 + (index * 0.1) }}
                className="flex h-[38px] sm:h-[42px] cursor-pointer items-center justify-center gap-[6px] rounded-lg 
                         border border-solid border-teal-500/30 bg-gradient-to-r from-teal-900/30 to-cyan-900/30 
                         backdrop-blur-sm px-2 sm:px-3 py-1 sm:py-2 hover:border-teal-500/60 hover:from-teal-900/40 
                         hover:to-cyan-900/40 transition-all duration-300 hover:shadow-lg hover:shadow-teal-900/20 min-w-[100px]"
                onClick={() => handleClickSuggestion(item?.name)}
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.98 }}
              >
                <img
                  src={item.icon}
                  alt={item.name}
                  width={18}
                  height={18}
                  className="w-[18px] sm:w-[20px] opacity-80 filter invert brightness-100"
                />
                <span className="text-xs sm:text-sm font-medium leading-[normal] text-gray-200">
                  {item.name}
                </span>
              </motion.div>
            ))}
          </AnimatePresence>
        </motion.div>
      </motion.div>

      {/* Magical premium gradient glow at the bottom */}
      <motion.div 
        initial={{ opacity: 0 }}
        animate={{ opacity: showGradient ? 1 : 0 }}
        transition={{ duration: 1.2 }}
        className="fixed bottom-0 left-0 right-0 h-[12px] z-50 overflow-hidden pointer-events-none"
      >
        <div className="relative w-full h-full">
          {/* Main perfect center glow with smooth fade at edges */}
          <div 
            className="absolute inset-0"
            style={{
              opacity: 0.85,
              background: 'radial-gradient(ellipse at center, rgba(12, 219, 182, 1) 0%, rgba(6, 219, 238, 0.7) 25%, rgba(6, 219, 238, 0.2) 50%, rgba(0, 0, 0, 0) 75%)',
              boxShadow: '0 0 30px 6px rgba(12, 219, 182, 0.5), 0 0 60px 10px rgba(6, 219, 238, 0.25)'
            }}
          />
          
          {/* Subtle shimmer overlay with perfect center focus */}
          <div 
            className="absolute inset-0"
            style={{
              animation: 'shimmer 8s ease-in-out infinite alternate',
              opacity: 0.5,
              background: 'radial-gradient(ellipse at center, rgba(255, 255, 255, 0.8) 0%, rgba(255, 255, 255, 0.2) 30%, rgba(255, 255, 255, 0) 60%)'
            }}
          />
          
          {/* Gentle breathing effect */}
          <div 
            className="absolute inset-0"
            style={{
              opacity: 0.4,
              animation: 'breathe 7s cubic-bezier(0.4, 0.0, 0.2, 1) infinite',
              background: 'radial-gradient(circle at center, rgba(255, 255, 255, 0.6) 0%, rgba(255, 255, 255, 0) 50%)'
            }}
          />
        </div>
      </motion.div>
      
      {/* Custom keyframes for magical animations */}
      <style jsx global>{`
        @keyframes shimmer {
          0% {
            opacity: 0.4;
            transform: scale(0.98);
          }
          50% {
            opacity: 0.6;
          }
          100% {
            opacity: 0.4;
            transform: scale(1.02);
          }
        }
        
        @keyframes breathe {
          0%, 100% {
            opacity: 0.3;
            transform: scale(0.96);
          }
          50% {
            opacity: 0.5;
            transform: scale(1.04);
          }
        }
      `}</style>
    </div>
  );
};

type suggestionType = {
  id: number;
  name: string;
  icon: string;
};

const suggestions: suggestionType[] = [
  {
    id: 1,
    name: "Stock analysis on ",
    icon: "/img/stock2.svg",
  },
  {
    id: 2,
    name: "Help me plan an adventure to ",
    icon: "/img/hiker.svg",
  },
  {
    id: 3,
    name: "What are the latest news on ",
    icon: "/img/news.svg",
  },
];

export default Hero;
