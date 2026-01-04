import React from 'react';
import './Button.css';

export function Button({ children, onClick, disabled = false, variant = 'primary', ...otherProps }) {
  
  const buttonClassName = `button-global button-${variant}`;

  return (
    <button
      className={buttonClassName} // 3. Use the new dynamic className
      onClick={onClick}
      disabled={disabled}
      {...otherProps}
    >
      {children}
    </button>
  );
}