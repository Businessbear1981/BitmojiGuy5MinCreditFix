import { NextResponse } from 'next/server'
import { generateMrBeeks, getSceneModel } from '@/lib/meshy'

let cachedGlbUrl: string | null = null
let generating = false

function sleep(ms: number) {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

export async function GET() {
  // Return cached URL if already generated
  if (cachedGlbUrl) {
    return NextResponse.json({ url: cachedGlbUrl, cached: true })
  }

  // Prevent duplicate generation
  if (generating) {
    return NextResponse.json({ status: 'generating', message: 'Mr Beeks is being created...' }, { status: 202 })
  }

  generating = true

  try {
    // Start generation
    const taskId = await generateMrBeeks()
    if (!taskId) {
      generating = false
      return NextResponse.json({ error: 'Failed to start generation' }, { status: 500 })
    }

    // Poll every 5 seconds until SUCCEEDED
    let attempts = 0
    const maxAttempts = 60 // 5 minutes max

    while (attempts < maxAttempts) {
      await sleep(5000)
      attempts++

      const result = await getSceneModel(taskId)

      if (result.status === 'SUCCEEDED' && result.model_urls?.glb) {
        cachedGlbUrl = result.model_urls.glb
        generating = false
        return NextResponse.json({
          url: cachedGlbUrl,
          thumbnail: result.thumbnail_url,
          taskId,
        })
      }

      if (result.status === 'FAILED') {
        generating = false
        return NextResponse.json({ error: 'Generation failed', taskId }, { status: 500 })
      }
    }

    generating = false
    return NextResponse.json({ error: 'Generation timed out', taskId }, { status: 504 })
  } catch (e) {
    generating = false
    return NextResponse.json({ error: String(e) }, { status: 500 })
  }
}
