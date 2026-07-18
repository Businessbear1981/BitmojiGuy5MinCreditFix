import { ButtonHTMLAttributes } from 'react';

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'fire' | 'ghost';
  full?: boolean;
}

export function Button({ variant = 'fire', full, className = '', children, ...props }: ButtonProps) {
  const base = 'inline-flex items-center justify-center gap-2 px-7 py-3.5 rounded-lg border-none cursor-pointer font-bangers text-xl tracking-wider uppercase transition-all duration-200 disabled:opacity-40 disabled:cursor-not-allowed disabled:transform-none';

  const variants = {
    fire: 'bg-gradient-to-br from-purple-500 to-purple-700 text-white shadow-[0_4px_24px_rgba(168,85,200,0.35),0_0_40px_rgba(168,85,200,0.1)] hover:shadow-[0_6px_32px_rgba(168,85,200,0.5),0_0_60px_rgba(168,85,200,0.15)] hover:-translate-y-0.5 active:scale-[0.98]',
    ghost: 'bg-transparent border border-teal-400/20 text-teal-400/70 text-sm font-sans font-medium normal-case tracking-normal hover:border-teal-400 hover:text-teal-400 hover:shadow-[0_0_12px_rgba(0,212,212,0.15)]',
  };

  return (
    <button
      className={`${base} ${variants[variant]} ${full ? 'w-full' : ''} ${className}`}
      {...props}
    >
      {children}
    </button>
  );
}
