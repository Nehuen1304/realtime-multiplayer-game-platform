import React from 'react';
import './Input.css'; // Import the component's styles

// This component is designed to be a flexible wrapper around the standard HTML <input>.
// It accepts all the standard input props (value, onChange, placeholder, type, etc.)
// via the `...otherProps` spread operator.
export function Input({ value, onChange, placeholder, type='text', maxLength=20,...otherProps }) {
  return (
    <input
      className="input-global" // Use a generic, global class name
      type={type}
      value={value}
      onChange={onChange}
      placeholder={placeholder}
      maxLength={maxLength}
      {...otherProps} // Pass down any other props like 'id', 'required', etc.
    />
  );
}