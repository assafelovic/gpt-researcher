import Image from "next/image";
import Link from "next/link";
import Modal from './Settings/Modal';

const Footer = () => {
  return (
    <>
      <div className="container flex min-h-[72px] items-center justify-between border-t border-[#D2D2D2] px-4 pb-3 pt-5 lg:min-h-[72px] lg:px-0 lg:py-5">
        <Modal />
        <div className="flex items-center gap-3">
          <Link href={"https://github.com/assafelovic/gpt-researcher"} target="_blank">
            <Image
              src={"/img/github-footer.svg"}
              alt="facebook"
              width={16}
              height={16}
            />{" "}
          </Link>
        </div>
      </div>
    </>
  );
};

export default Footer;