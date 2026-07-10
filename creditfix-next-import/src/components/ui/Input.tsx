import { InputHTMLAttributes, SelectHTMLAttributes } from 'react';

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label: string;
}

export function Input({ label, className = '', ...props }: InputProps) {
  return (
    <div className="mb-4">
      <label className="block text-xs font-bold tracking-wide uppercase text-gray-500 mb-1.5">
        {label}
      </label>
      <input
        className={`w-full bg-teal-400/[0.03] border border-teal-400/15 rounded-lg px-4 py-3 text-gray-200 font-sans text-[15px] outline-none transition-all duration-200 placeholder:text-gray-600 focus:border-teal-400 focus:shadow-[0_0_0_3px_rgba(0,212,212,0.1),0_0_12px_rgba(0,212,212,0.15)] ${className}`}
        {...props}
      />
    </div>
  );
}

interface SelectProps extends SelectHTMLAttributes<HTMLSelectElement> {
  label: string;
  options: Array<{ value: string; label: string }>;
}

export function Select({ label, options, className = '', ...props }: SelectProps) {
  return (
    <div className="mb-4">
      <label className="block text-xs font-bold tracking-wide uppercase text-gray-500 mb-1.5">
        {label}
      </label>
      <select
        className={`w-full bg-teal-400/[0.03] border border-teal-400/15 rounded-lg px-4 py-3 text-gray-200 font-sans text-[15px] outline-none appearance-none transition-all duration-200 focus:border-teal-400 focus:shadow-[0_0_0_3px_rgba(0,212,212,0.1)] bg-[url("data:image/svg+xml,%3Csvg%20xmlns='http://www.w3.org/2000/svg'%20width='12'%20height='8'%3E%3Cpath%20d='M1%201l5%205%205-5'%20stroke='%23666'%20stroke-width='1.5'%20fill='none'/%3E%3C/svg%3E")] bg-no-repeat bg-[right_16px_center] ${className}`}
        {...props}
      >
        {options.map((o) => (
          <option key={o.value} value={o.value} className="bg-[#0A0A10] text-gray-200">
            {o.label}
          </option>
        ))}
      </select>
    </div>
  );
}
