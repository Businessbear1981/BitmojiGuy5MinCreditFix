import { Composition } from 'remotion'
import { MyComposition } from './Composition'

export const RemotionRoot: React.FC = () => (
  <Composition
    id="MyComposition"
    component={MyComposition}
    durationInFrames={150}
    fps={30}
    width={1920}
    height={1080}
    defaultProps={{ title: 'BitmojiGuy 5-Min CreditFix' }}
  />
)
