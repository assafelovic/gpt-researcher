import { NextResponse } from "next/server";
import Together from "together-ai";
import { z } from "zod";
import { zodToJsonSchema } from "zod-to-json-schema";

const together = new Together({
  apiKey: process.env["TOGETHER_API_KEY"],
  baseURL: "https://together.helicone.ai/v1",
  defaultHeaders: {
    "Helicone-Auth": `Bearer ${process.env.HELICONE_API_KEY}`,
  },
});

export async function POST(request: Request) {
  let { question } = await request.json();

  const schema = z.array(z.string()).length(3);
  const jsonSchema = zodToJsonSchema(schema, "mySchema");

  const similarQuestions = await together.chat.completions.create({
    messages: [
      {
        role: "system",
        content: `
          You are a helpful assistant that helps the user to ask related questions, based on user's original question. Please identify worthwhile topics that can be follow-ups, and write 3 questions no longer than 20 words each. Please make sure that specifics, like events, names, locations, are included in follow up questions so they can be asked standalone. For example, if the original question asks about "the Manhattan project", in the follow up question, do not just say "the project", but use the full name "the Manhattan project". Your related questions must be in the same language as the original question.

          Please provide these 3 related questions as a JSON array of 3 strings. Do NOT repeat the original question. ONLY return the JSON array, I will get fired if you don't return JSON. Here is the user's original question:`,
      },
      {
        role: "user",
        content: question,
      },
    ],
    // @ts-ignore
    response_format: { type: "json_object", schema: jsonSchema },
    model: "mistralai/Mixtral-8x7B-Instruct-v0.1",
  });

  let questions = similarQuestions.choices?.[0].message?.content || "[]";

  return NextResponse.json(JSON.parse(questions));
}
