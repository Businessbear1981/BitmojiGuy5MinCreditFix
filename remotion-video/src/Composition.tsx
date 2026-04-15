import { AbsoluteFill, interpolate, useCurrentFrame } from 'remotion'

export const MyComposition: React.FC<{ title: string }> = ({ title }) => {
  const frame = useCurrentFrame()
  const opacity = interpolate(frame, [0, 30], [0, 1], { extrapolateRight: 'clamp' })

  return (
    <AbsoluteFill style={{ background: '#0A0806', color: '#F0D080', fontFamily: 'serif' }}>
      <div style={{ margin: 'auto', fontSize: 96, letterSpacing: 4, opacity }}>{title}</div>
    </AbsoluteFill>
  )
}
