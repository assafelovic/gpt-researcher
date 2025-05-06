import Image from "next/image";

const SimilarTopics = ({
  similarQuestions,
  handleDisplayResult,
  reset,
}: {
  similarQuestions: string[];
  handleDisplayResult: (item: string) => void;
  reset: () => void;
}) => {
  return (
    <div className="container flex h-auto w-full shrink-0 gap-4 rounded-lg border border-solid border-[#C2C2C2] bg-white p-5 lg:p-10">
      <div className="hidden lg:block">
        <Image
          src="/img/similarTopics.svg"
          alt="footer"
          width={24}
          height={24}
        />
      </div>
      <div className="flex-1 divide-y divide-[#E5E5E5]">
        <div className="flex gap-4 pb-3">
          <Image
            src="/img/similarTopics.svg"
            alt="footer"
            width={24}
            height={24}
            className="block lg:hidden"
          />
          <h3 className="text-base font-bold uppercase text-black">
            Similar topics:{" "}
          </h3>
        </div>

        <div className="max-w-[890px] space-y-[15px] divide-y divide-[#E5E5E5]">
          {similarQuestions.length > 0 ? (
            similarQuestions.map((item) => (
              <button
                className="flex cursor-pointer items-center gap-4 pt-3.5"
                key={item}
                onClick={() => {
                  reset();
                  handleDisplayResult(item);
                }}
              >
                <div className="flex items-center">
                  <Image
                    src="/img/arrow-circle-up-right.svg"
                    alt="footer"
                    width={24}
                    height={24}
                  />
                </div>
                <p className="text-sm font-light leading-[normal] text-[#1B1B16] [leading-trim:both] [text-edge:cap]">
                  {item}
                </p>
              </button>
            ))
          ) : (
            <>
              <div className="h-10 w-full animate-pulse rounded-md bg-gray-300" />
              <div className="h-10 w-full animate-pulse rounded-md bg-gray-300" />
              <div className="h-10 w-full animate-pulse rounded-md bg-gray-300" />
            </>
          )}
        </div>
      </div>
    </div>
  );
};

export default SimilarTopics;
