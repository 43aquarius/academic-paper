// LLM query helper: reads a JSON request from stdin, writes JSON to stdout.
// Request:  { system: string, user: string, temperature: number }
// Response: { ok: boolean, content: string, usage?: object, error?: string }
import ZAI from '/home/z/.bun/install/global/node_modules/z-ai-web-dev-sdk/dist/index.js';
import process from 'process';

async function main() {
  let req;
  const chunks = [];
  for await (const chunk of process.stdin) chunks.push(chunk);
  const raw = Buffer.concat(chunks).toString('utf8');
  try {
    req = JSON.parse(raw);
  } catch (e) {
    console.log(JSON.stringify({ ok: false, error: `bad stdin json: ${e.message}` }));
    return;
  }

  const retries = 8;
  let lastErr = null;
  let attempts = 0;
  for (let attempt = 1; attempt <= retries; attempt++) {
    attempts = attempt;
    try {
      const zai = await ZAI.create();
      const body = {
        messages: [
          { role: 'assistant', content: req.system },
          { role: 'user', content: req.user },
        ],
        temperature: typeof req.temperature === 'number' ? req.temperature : 0,
        thinking: { type: 'disabled' },
        max_tokens: 96,
      };
      if (req.model) body.model = req.model;
      const completion = await zai.chat.completions.create(body);
      const content = completion.choices?.[0]?.message?.content;
      if (!content || content.trim().length === 0) throw new Error('empty response');
      console.log(JSON.stringify({
        ok: true,
        content: content.trim(),
        usage: completion.usage || null,
        model: completion.model || null,
        attempts,
      }));
      return;
    } catch (e) {
      lastErr = e;
      // Exponential backoff with jitter; 429 needs longer waits.
      const base = /429|Too many/i.test(String(e.message)) ? 3 : 2;
      const wait = Math.min(base * Math.pow(2, attempt - 1), 45) * (0.8 + Math.random() * 0.4);
      await new Promise(r => setTimeout(r, wait * 1000));
    }
  }
  console.log(JSON.stringify({ ok: false, error: String(lastErr && lastErr.message), attempts }));
}

main().catch(e => {
  console.log(JSON.stringify({ ok: false, error: String(e.message) }));
  process.exit(0);
});
