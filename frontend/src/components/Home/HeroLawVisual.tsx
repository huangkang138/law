import Image from 'next/image';

import HeroOrbit from './HeroOrbit';
import styles from './HomePage.module.css';

export default function HeroLawVisual() {
  return (
    <div className={`${styles.lawVisual} ${styles.heroCore}`} aria-label="律知法律智能服务标识">
      <HeroOrbit layer="back" />

      <div className={styles.platform} aria-hidden="true">
        <Image
          src="/home/lvzhi-platform.png"
          alt=""
          fill
          priority
          sizes="(max-width: 768px) 420px, 680px"
          className={styles.visualImage}
        />
      </div>

      <div className={styles.platformRipple} aria-hidden="true">
        <span />
        <span />
        <span />
      </div>

      <div className={styles.coreShadow} aria-hidden="true" />

      <div className={styles.heroLogo}>
        <Image
          src="/home/lvzhi-logo.png"
          alt="律知蓝青紫花瓣天平 Logo"
          fill
          priority
          sizes="(max-width: 768px) 210px, 338px"
          className={styles.visualImage}
        />
      </div>

      <HeroOrbit layer="front" />
    </div>
  );
}
