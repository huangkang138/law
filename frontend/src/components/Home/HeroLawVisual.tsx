import Image from 'next/image';

import styles from './HomePage.module.css';

export default function HeroLawVisual() {
  return (
    <div className={styles.lawVisual} aria-label="律知法律智能服务标识">
      <div className={styles.orbit} aria-hidden="true">
        <Image
          src="/home/lvzhi-orbit.png"
          alt=""
          fill
          sizes="(max-width: 768px) 390px, 590px"
          className={styles.visualImage}
        />
      </div>

      <div className={styles.logoFloat}>
        <Image
          src="/home/lvzhi-logo.png"
          alt="律知蓝青紫花瓣天平 Logo"
          fill
          priority
          sizes="(max-width: 768px) 210px, 338px"
          className={styles.visualImage}
        />
      </div>

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
    </div>
  );
}
