import Link from 'next/link';
import type { LucideIcon } from 'lucide-react';

import styles from './HomePage.module.css';

interface HeroFeatureCardProps {
  title: string;
  description: string;
  href: string;
  icon: LucideIcon;
  positionClassName: string;
  delay: string;
}

export default function HeroFeatureCard({
  title,
  description,
  href,
  icon: Icon,
  positionClassName,
  delay,
}: HeroFeatureCardProps) {
  return (
    <Link
      href={href}
      className={`${styles.featureCard} ${positionClassName}`}
      style={{ animationDelay: delay }}
    >
      <span className={styles.featureIcon} aria-hidden="true">
        <Icon size={25} strokeWidth={1.8} />
      </span>
      <span className={styles.featureCopy}>
        <strong>{title}</strong>
        <small>{description}</small>
      </span>
      <span className={styles.featureArrow} aria-hidden="true">→</span>
    </Link>
  );
}
