// Single-shot API probe (no retries). Prints PROBE_OK or PROBE_FAIL.
import ZAI from '/home/z/.bun/install/global/node_modules/z-ai-web-dev-sdk/dist/index.js';
try {
  const zai = await ZAI.create();
  const r = await zai.chat.completions.create({
    messages: [{ role: 'user', content: 'Say OK' }],
    max_tokens: 4, temperature: 0, thinking: { type: 'disabled' }
  });
  const c = r.choices?.[0]?.message?.content || '';
  console.log(c.trim() ? 'PROBE_OK' : 'PROBE_FAIL');
} catch (e) {
  console.log('PROBE_FAIL');
}
