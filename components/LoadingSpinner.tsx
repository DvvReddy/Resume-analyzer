// components/LoadingSpinner.tsx
'use client';

import clsx from 'clsx';

interface LoadingSpinnerProps {
  className?: string;
}

export default function LoadingSpinner({ className }: LoadingSpinnerProps) {
  return (
    <span
      className={clsx(
        'inline-block h-4 w-4 animate-spin rounded-full border-[2px] border-emerald-300 border-t-transparent align-middle',
        className
      )}
      aria-hidden="true"
    />
  );
}
