import React from 'react';
import './Window.css';

/**
 * A general-purpose Window container component.
 * @param {object} props
 * @param {React.ReactNode} props.children - The content to be displayed inside the window.
 * @param {string} [props.title] - An optional title to display at the top of the window.
 */
export function Window({ children, title, ...otherProps }) {
  return (
    // The main container div. We pass any other props to it.
    <div className="window-container" {...otherProps}>
      {/* Conditionally render a title if one is provided */}
      {title && <h2 className="window-title">{title}</h2>}
      
      {/* Render the content passed into the component */}
      {children}
    </div>
  );
}