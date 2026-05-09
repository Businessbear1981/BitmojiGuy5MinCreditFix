// BitmojiGuy 5-Min Credit Fix — Meshy AI 3D Generation
// AE Labs — (c) 2025 Sean Gilmore / Arden Edge Capital

const MESHY_API = 'https://api.meshy.ai/openapi/v2'
const MESHY_KEY = process.env.MESHY_API_KEY ?? ''

async function meshyPost(endpoint: string, body: object) {
  const res = await fetch(`${MESHY_API}${endpoint}`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${MESHY_KEY}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(body),
  })
  return res.json()
}

async function meshyGet(endpoint: string) {
  const res = await fetch(`${MESHY_API}${endpoint}`, {
    headers: { 'Authorization': `Bearer ${MESHY_KEY}` },
  })
  return res.json()
}

// ─── WARRIOR MODEL ───────────────────────────────────────────────────────────

export async function generateWarrior(): Promise<string> {
  const data = await meshyPost('/text-to-3d', {
    mode: 'preview',
    prompt: 'Japanese samurai warrior full armor kabuto helmet lamellar chest plate kote arm guards katana Demon Slayer anime style dark gold',
    art_style: 'realistic',
    negative_prompt: 'cartoon simple flat bright modern',
  })
  return data.result as string
}

export async function getWarriorModel(taskId: string): Promise<{
  status: string
  model_urls?: { glb?: string; fbx?: string; obj?: string }
  thumbnail_url?: string
  progress?: number
}> {
  const data = await meshyGet(`/text-to-3d/${taskId}`)
  return {
    status: data.status,
    model_urls: data.model_urls,
    thumbnail_url: data.thumbnail_url,
    progress: data.progress,
  }
}

// ─── SCENE ASSETS ────────────────────────────────────────────────────────────

export async function generateScene(prompt: string, negativePrompt?: string): Promise<string> {
  const data = await meshyPost('/text-to-3d', {
    mode: 'preview',
    prompt,
    art_style: 'realistic',
    negative_prompt: negativePrompt ?? 'bright cartoon low quality modern',
  })
  return data.result as string
}

export async function getSceneModel(taskId: string): Promise<{
  status: string
  model_urls?: { glb?: string; fbx?: string; obj?: string }
  thumbnail_url?: string
  progress?: number
}> {
  return meshyGet(`/text-to-3d/${taskId}`)
}

// ─── BATCH STATUS CHECK ──────────────────────────────────────────────────────

export async function checkAllJobs(taskIds: string[]): Promise<Array<{
  id: string
  status: string
  progress?: number
  thumbnail_url?: string
  model_urls?: { glb?: string }
}>> {
  const results = await Promise.all(
    taskIds.map(async (id) => {
      const data = await meshyGet(`/text-to-3d/${id}`)
      return {
        id,
        status: data.status,
        progress: data.progress,
        thumbnail_url: data.thumbnail_url,
        model_urls: data.model_urls,
      }
    })
  )
  return results
}

// ─── SCENE PROMPTS (Demon Slayer cinematic) ──────────────────────────────────

export const SCENE_PROMPTS = {
  scene1_dojo: 'Dark Japanese dojo interior, wooden walls with timber grain, armor stand with samurai kabuto helmet and chest plate, katana leaning, candlelight glow, moonlight shaft through window onto wooden floor, incense smoke, cinematic anime style like Demon Slayer, dark moody atmospheric, ominous shadow on wall',
  scene2_koi: 'Japanese koi pond at night, six colorful koi fish swimming beneath dark water, moonlit water surface with shimmer, lily pads, reed grass, something lurking deep beneath, Demon Slayer anime cinematic dark atmospheric',
  scene3_temple: 'Steep ancient Japanese temple stone steps ascending into darkness, Kill Bill aesthetic, night scene with moon, pine trees flanking, stone lanterns, misty Natagumo mountain, two silhouette figures climbing, temple with faint red glow at top, Demon Slayer anime cinematic',
  scene4_garden: 'Japanese zen rock garden at night, raked sand with concentric ripple patterns around dark stones, bamboo grove on sides, stone lantern glowing faintly, claw marks in sand, dark cloud overhead, Demon Slayer anime cinematic dark atmospheric',
  scene5_gate: 'Japanese crimson torii gate at night, cherry blossom trees in full bloom flanking, petals drifting through gate opening, stone path receding, moonlit stars, massive dark dragon silhouette barely visible beyond gate with red eyes, Demon Slayer anime cinematic',
  warrior: 'Japanese samurai warrior in dark underrobe standing in ready stance, detached armor pieces: kabuto helmet with golden crescent maedate, do chest plate with gold lamellar scales and mon crest, kote arm guards, katana with gold tsuba guard, Demon Slayer anime style dark cinematic',
  mrBeeks: 'small crocheted yellow duck chibi mascot, round yarn body, orange beak, button eyes, dangly rust legs, tiny yellow boots, holding tiny white sign, Unravel game style',
}

// ─── MR BEEKS MASCOT ─────────────────────────────────────────────────────────

export async function generateMrBeeks(): Promise<string> {
  const data = await meshyPost('/text-to-3d', {
    mode: 'preview',
    prompt: SCENE_PROMPTS.mrBeeks,
    art_style: 'realistic',
    negative_prompt: 'realistic human, scary, dark, low quality',
  })
  return data.result as string
}
