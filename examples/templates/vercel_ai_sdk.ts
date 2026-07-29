/**
 * Vercel AI SDK — custom OpenAI-compatible provider pointed at Ohm.
 *
 * Prefer LOCAL until https://api.withohm.dev/v1 answers chat (docs/PLATFORM.md).
 *
 *   npm i ai @ai-sdk/openai
 */
import { createOpenAI } from "@ai-sdk/openai";
import { generateText } from "ai";

const baseURL =
  process.env.OHM_BASE_URL ?? "http://127.0.0.1:8081/v1";
const apiKey = process.env.OHM_API_KEY ?? "sk-at-dev";

export const ohm = createOpenAI({
  apiKey,
  baseURL,
  name: "ohm",
});

export async function demo() {
  const { text } = await generateText({
    model: ohm("mock"),
    prompt: "Say hi in one word",
  });
  return text;
}

if (import.meta.url === `file://${process.argv[1]}`) {
  demo().then(console.log).catch(console.error);
}
