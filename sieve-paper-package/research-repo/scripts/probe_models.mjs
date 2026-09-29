// Multi-model probe: tests whether different models have independent quotas.
// Usage: node scripts/probe_models.mjs [model1 model2 ...]
import ZAI from '/home/z/.bun/install/global/node_modules/z-ai-web-dev-sdk/dist/index.js';

const models = process.argv.slice(2).length
  ? process.argv.slice(2)
  : ['glm-4-plus', 'glm-4-flash', 'glm-4-air', 'glm-4-long',
     'glm-4.5', 'glm-4.6', 'glm-4v-plus'];

for (const m of models) {
  try {
    const zai = await ZAI.create();
    const r = await zai.chat.completions.create({
      model: m,
      messages: [{ role: 'user', content: 'Say OK' }],
      max_tokens: 4, temperature: 0, thinking: { type: 'disabled' }
    });
    const c = r.choices?.[0]?.message?.content || '';
    const served = r.model || '?';
    console.log(c.trim() ? `OK ${m} -> served:${served}` : `EMPTY ${m}`);
  } catch (e) {
    const msg = String(e.message).slice(0, 90).replace(/\n/g, ' ');
    console.log(`FAIL ${m} :: ${msg}`);
  }
}
