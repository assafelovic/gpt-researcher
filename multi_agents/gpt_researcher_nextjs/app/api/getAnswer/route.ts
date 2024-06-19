import { Readability } from "@mozilla/readability";
import jsdom, { JSDOM } from "jsdom";
import {
  TogetherAIStream,
  TogetherAIStreamPayload,
} from "@/utils/TogetherAIStream";
import Together from "together-ai";

const together = new Together({
  apiKey: process.env["TOGETHER_API_KEY"],
  baseURL: "https://together.helicone.ai/v1",
  defaultHeaders: {
    "Helicone-Auth": `Bearer ${process.env.HELICONE_API_KEY}`,
  },
});

export async function POST(request: Request) {
  let { question, sources } = await request.json();

  let finalResults = await Promise.all(
    sources.map(async (result: any) => {
      try {
        const response = await fetch(result.url);
        const html = await response.text();
        const virtualConsole = new jsdom.VirtualConsole();
        const dom = new JSDOM(html, { virtualConsole });

        const doc = dom.window.document;
        const parsed = new Readability(doc).parse();
        let parsedContent = parsed
          ? cleanedText(parsed.textContent)
          : "Nothing found";

        return {
          ...result,
          fullContent: parsedContent,
        };
      } catch (e) {
        console.log(`error parsing ${result.name}, error: ${e}`);
        return {
          ...result,
          fullContent: "not available",
        };
      }
    }),
  );

  const mainAnswerPrompt = `
  Given a user question and some context, please write a clean, concise and accurate answer to the question based on the context. You will be given a set of related contexts to the question, each starting with a reference number like [[citation:x]], where x is a number. Please use the context when crafting your answer.

  Your answer must be correct, accurate and written by an expert using an unbiased and professional tone. Please limit to 1024 tokens. Do not give any information that is not related to the question, and do not repeat. Say "information is missing on" followed by the related topic, if the given context do not provide sufficient information.

  Here are the set of contexts:

  <contexts>
  ${finalResults.map(
    (result, index) => `[[citation:${index}]] ${result.fullContent} \n\n`,
  )}
  </contexts>

  Remember, don't blindly repeat the contexts verbatim and don't tell the user how you used the citations – just respond with the answer. It is very important for my career that you follow these instructions. Here is the user question:
    `;

  try {
    const payload: TogetherAIStreamPayload = {
      model: "mistralai/Mixtral-8x7B-Instruct-v0.1",
      messages: [
        { role: "system", content: mainAnswerPrompt },
        {
          role: "user",
          content: question,
        },
      ],
      stream: true,
    };

    const stream = await TogetherAIStream(payload);
    return new Response(stream, {
      headers: new Headers({
        "Cache-Control": "no-cache",
      }),
    });
  } catch (e) {
    // If for some reason streaming fails, we can just call it without streaming
    let answer = await together.chat.completions.create({
      model: "mistralai/Mixtral-8x7B-Instruct-v0.1",
      messages: [
        { role: "system", content: mainAnswerPrompt },
        {
          role: "user",
          content: question,
        },
      ],
    });

    let parsedAnswer = answer.choices![0].message?.content;
    console.log("Error is: ", e);
    return new Response(parsedAnswer, { status: 202 });
  }
}

const cleanedText = (text: string) => {
  let newText = text
    .trim()
    .replace(/(\n){4,}/g, "\n\n\n")
    .replace(/\n\n/g, " ")
    .replace(/ {3,}/g, "  ")
    .replace(/\t/g, "")
    .replace(/\n+(\s*\n)*/g, "\n");

  return newText.substring(0, 20000);
};
