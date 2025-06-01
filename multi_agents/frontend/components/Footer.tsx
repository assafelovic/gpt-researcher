import Image from "next/image";
import Link from "next/link";
import Modal from './Settings/Modal';

const Footer = ({ setChatBoxSettings, chatBoxSettings}) => {
  
  return (
    <>
      <div className="container flex min-h-[72px] items-center justify-between border-t border-[#D2D2D2] px-4 pb-3 pt-5 lg:min-h-[72px] lg:px-0 lg:py-5">
        <Modal setChatBoxSettings={setChatBoxSettings} chatBoxSettings={chatBoxSettings} />
        <div className="flex items-center gap-3">
          <Link href={"https://hub.docker.com/r/gptresearcher/gpt-researcher"} target="_blank">
              <Image
                src={"/img/docker-blue.svg"}
                alt="docker"
                width={35}
                height={35}
              />{" "}
          </Link>
          <Link href={"https://github.com/assafelovic/gpt-researcher"} target="_blank">
            <Image
              src={"/img/github-blue.svg"}
              alt="github"
              width={35}
              height={35}
            />{" "}
          </Link>
        </div>
      </div>
    </>
  );
};

export default Footer;