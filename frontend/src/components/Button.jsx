import { useState } from "react";

export default function Button({
  children,
  variant = "primary",
  className = "",
  onPointerDown,
  ...props
}) {
  const [ripples, setRipples] = useState([]);

  function handlePointerDown(event) {
    const rect = event.currentTarget.getBoundingClientRect();
    setRipples((current) => [
      ...current,
      {
        id: `${Date.now()}-${Math.random()}`,
        x: event.clientX - rect.left,
        y: event.clientY - rect.top,
        size: Math.max(rect.width, rect.height) * 2.4,
      },
    ]);
    onPointerDown?.(event);
  }

  return (
    <button
      className={`button button-${variant} ${className}`.trim()}
      onPointerDown={handlePointerDown}
      {...props}
    >
      <span className="button-label">{children}</span>
      {ripples.map((ripple) => (
        <span
          key={ripple.id}
          className="ripple"
          style={{
            left: ripple.x,
            top: ripple.y,
            width: ripple.size,
            height: ripple.size,
          }}
          onAnimationEnd={() =>
            setRipples((current) => current.filter((item) => item.id !== ripple.id))
          }
        />
      ))}
    </button>
  );
}
