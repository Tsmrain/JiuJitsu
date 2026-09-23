import { useEffect, useRef } from 'react';
import './ProgressRing.css';

export default function ProgressRing({ value = 0, statusText = "Processing" }) {
  const progressRef = useRef(null);

  // Fallback for browsers that don't support `attr()` CSS function for properties yet
  useEffect(() => {
    if (progressRef.current && !CSS.supports("width: attr(value type(<number>))")) {
      progressRef.current.style.setProperty("--value", value);
    }
  }, [value]);

  return (
    <div className="ring-wrapper">
      <progress 
        ref={progressRef}
        value={value} 
        max="100" 
        aria-label={`Upload and analysis progress: ${value}%`} 
        className="progress-ring"
      ></progress>
      <div className="ring-content">
        <span className="ring-percentage">{Math.round(value)}%</span>
        <span className="ring-status">{statusText}</span>
      </div>
    </div>
  );
}
