// components/ui/Button.tsx
'use client';

import '../../css/Button.css';
import type { ButtonHTMLAttributes, ReactNode } from 'react';
import clsx from 'clsx';

type Variant = 'primary' | 'secondary' | 'ghost';

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
  children: ReactNode;
}

export default function Button({
  variant = 'primary',
  className,
  children,
  ...props
}: ButtonProps) {
  const variantClass: Record<Variant, string> = {
    primary: 'btn-primary btn-active', // primary is always green / selected
    secondary: 'btn-secondary',
    ghost: 'btn-ghost',
  };

  return (
    <button
      className={clsx('btn', variantClass[variant], className)}
      {...props}
    >
      {children}
    </button>
  );
}
