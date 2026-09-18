import styles from './HeroOrbit.module.css';
import type { CSSProperties } from 'react';

type HeroOrbitProps = {
  layer: 'back' | 'front';
};

const MAIN_ORBIT =
  'M 89 232 A 260 82 -15 1 1 591 98 A 260 82 -15 1 1 89 232 Z';
const AUXILIARY_ORBIT =
  'M 89 322 A 260 82 -15 1 1 591 188 A 260 82 -15 1 1 89 322 Z';
const ORBIT_PERSPECTIVE = 'translate(340 258) rotate(-4) scale(1.04 0.88) translate(-340 -250)';

function OrbitTrack({ path, className }: { path: string; className: string }) {
  return (
    <g className={className}>
      <path className={styles.trackGlow} d={path} />
      <path className={styles.trackBody} d={path} />
      <path className={styles.trackHighlight} d={path} />
    </g>
  );
}

function OrbitBall({ orbit }: { orbit: 'upper' | 'lower' }) {
  const radius = 15;

  return (
    <g className={orbit === 'upper' ? styles.ballUpper : styles.ballLower}>
      <g className={styles.ballDepth}>
        <circle className={styles.ballGlow} r={radius + 7} />
        <circle className={styles.ballBody} r={radius} />
        <ellipse
          className={styles.ballHighlight}
          cx={-radius * 0.3}
          cy={-radius * 0.35}
          rx={radius * 0.34}
          ry={radius * 0.2}
        />
      </g>
    </g>
  );
}

export default function HeroOrbit({ layer }: HeroOrbitProps) {
  const isFront = layer === 'front';

  return (
    <svg
      className={`${styles.orbitLayer} ${isFront ? styles.orbitFront : styles.orbitBack}`}
      viewBox="0 0 680 500"
      preserveAspectRatio="xMidYMid meet"
      aria-hidden="true"
    >
      <defs>
        <linearGradient id={`orbit-stroke-${layer}`} x1="0" y1="0" x2="1" y2="1">
          <stop offset="0" stopColor="#dff8ff" />
          <stop offset="0.42" stopColor="#91c8ff" />
          <stop offset="0.76" stopColor="#7c9cff" />
          <stop offset="1" stopColor="#b79cff" />
        </linearGradient>
        <radialGradient id={`orbit-ball-${layer}`} cx="32%" cy="25%" r="78%">
          <stop offset="0" stopColor="#f5fdff" />
          <stop offset="0.2" stopColor="#69ddff" />
          <stop offset="0.62" stopColor="#397df1" />
          <stop offset="1" stopColor="#8c62e9" />
        </radialGradient>
        <filter id={`orbit-glow-${layer}`} x="-40%" y="-40%" width="180%" height="180%">
          <feGaussianBlur stdDeviation="9" />
        </filter>
        <filter id={`ball-glow-${layer}`} x="-80%" y="-80%" width="260%" height="260%">
          <feGaussianBlur stdDeviation="6" />
        </filter>
        <linearGradient id={`front-fade-${layer}`} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor="black" />
          <stop offset="0.46" stopColor="black" />
          <stop offset="0.58" stopColor="white" />
          <stop offset="1" stopColor="white" />
        </linearGradient>
        <linearGradient id={`back-fade-${layer}`} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor="white" />
          <stop offset="0.46" stopColor="white" />
          <stop offset="0.58" stopColor="black" />
          <stop offset="1" stopColor="black" />
        </linearGradient>
        <mask id={`front-mask-${layer}`}>
          <rect width="680" height="500" fill={`url(#front-fade-${layer})`} />
        </mask>
        <mask id={`back-mask-${layer}`}>
          <rect width="680" height="500" fill={`url(#back-fade-${layer})`} />
        </mask>
      </defs>

      <g
        className={styles.trackGroup}
        style={{ '--orbit-stroke': `url(#orbit-stroke-${layer})` } as CSSProperties}
        mask={`url(#${isFront ? 'front' : 'back'}-mask-${layer})`}
        transform={ORBIT_PERSPECTIVE}
      >
        <OrbitTrack path={MAIN_ORBIT} className={styles.mainOrbitFloat} />
        <OrbitTrack path={AUXILIARY_ORBIT} className={styles.auxiliaryOrbitFloat} />
      </g>

      <g
        className={styles.ballGroup}
        style={
          {
            '--orbit-ball-fill': `url(#orbit-ball-${layer})`,
            '--orbit-ball-glow': `url(#orbit-ball-${layer})`,
            '--main-orbit-path': `path('${MAIN_ORBIT}')`,
            '--auxiliary-orbit-path': `path('${AUXILIARY_ORBIT}')`,
          } as CSSProperties
        }
        mask={`url(#${isFront ? 'front' : 'back'}-mask-${layer})`}
        transform={ORBIT_PERSPECTIVE}
      >
        <g className={styles.mainOrbitFloat}>
          <OrbitBall orbit="upper" />
        </g>
        <g className={styles.auxiliaryOrbitFloat}>
          <OrbitBall orbit="lower" />
        </g>
      </g>
    </svg>
  );
}
