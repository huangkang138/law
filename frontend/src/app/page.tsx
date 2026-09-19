import { BookOpenCheck, FileSearch, FileText, HeartHandshake, MessageSquareText, Scale, ShieldCheck, Zap } from 'lucide-react';

import HeroFeatureCard from '@/components/Home/HeroFeatureCard';
import HeroLawVisual from '@/components/Home/HeroLawVisual';
import styles from '@/components/Home/HomePage.module.css';

const heroFeatures = [
  {
    title: '普法问答',
    description: '随时解答法律疑问',
    href: '/chat',
    icon: MessageSquareText,
    positionClassName: styles.featureLeftTop,
    delay: '-0.8s',
  },
  {
    title: '合同审查',
    description: '智能识别法律风险',
    href: '/contract',
    icon: FileText,
    positionClassName: styles.featureLeftBottom,
    delay: '-2.1s',
  },
  {
    title: '法律检索',
    description: '精准获取法律依据',
    href: '/case-analysis',
    icon: FileSearch,
    positionClassName: styles.featureRightTop,
    delay: '-1.4s',
  },
  {
    title: '风险预警',
    description: '防患于未然',
    href: '/dispute-center',
    icon: ShieldCheck,
    positionClassName: styles.featureRightBottom,
    delay: '-2.7s',
  },
];

const values = [
  { title: '更公平', description: '让法律更普惠，守护每个人的合法权益', icon: Scale },
  { title: '更专业', description: '基于权威法律知识，提供准确的解答', icon: BookOpenCheck },
  { title: '更高效', description: 'AI赋能法律服务，提升效率，直达答案', icon: Zap },
  { title: '更温暖', description: '让优质法律服务走进生活', icon: HeartHandshake },
];

export default function HomePage() {
  return (
    <div className={styles.pageShell}>
      <section className={styles.hero} aria-labelledby="home-hero-title">
        <div className={styles.backgroundLayers} aria-hidden="true">
          <span className={styles.backgroundCurveLeft} />
          <span className={styles.backgroundCurveRight} />
          <span className={styles.backgroundGlowBottom} />
          <span className={styles.backgroundBallLeft} />
          <span className={styles.backgroundBallRight} />
        </div>

        <div className={styles.heroLayout}>
          <div className={styles.heroStage}>
            <aside className={`${styles.sideSlogan} ${styles.sideSloganLeft}`} aria-label="品牌理念">
              <span className={styles.sloganLine} />
              <p>以 专 业 之 力</p>
              <p>守 护 每 一 次 选 择</p>
            </aside>

            {heroFeatures.map((feature) => (
              <HeroFeatureCard key={feature.title} {...feature} />
            ))}

            <HeroLawVisual />

            <aside className={`${styles.sideSlogan} ${styles.sideSloganRight}`} aria-label="服务理念">
              <span className={styles.sloganLine} />
              <p>让</p>
              <p>法 律 服 务</p>
              <p>触 手 可 及</p>
            </aside>
          </div>

          <div className={styles.heroCopy}>
            <h1 id="home-hero-title">
              <span className={styles.titlePrimaryGradient}>知法于心</span>
              <span className={styles.titleDivider} aria-hidden="true" />
              <span className={styles.titleGradient}>行法于行</span>
            </h1>
            <p>用 AI 让法律服务更简单、更可靠</p>
            <div className={styles.titleIndicator} aria-hidden="true">
              <span />
              <i />
              <i />
              <span />
            </div>
          </div>
        </div>

        <div className={styles.valueBar} aria-label="平台价值">
          {values.map(({ title, description, icon: Icon }) => (
            <div className={styles.valueItem} key={title}>
              <span className={styles.valueIcon} aria-hidden="true"><Icon size={22} strokeWidth={1.8} /></span>
              <span>
                <strong>{title}</strong>
                <small>{description}</small>
              </span>
            </div>
          ))}
        </div>

        <div className={styles.valueTagline} aria-hidden="true">
          <span />
          <p>科技让法治更美好</p>
          <span />
        </div>
      </section>

      <footer className={styles.footer}>
        <span>© 2026 律知智能法律服务平台</span>
      </footer>
    </div>
  );
}
