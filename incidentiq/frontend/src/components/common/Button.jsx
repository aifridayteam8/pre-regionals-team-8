export default function Button({
  children,
  variant = "secondary",
  size = "md",
  type = "button",
  disabled = false,
  onClick,
  className = "",
}) {
  const classes = ["btn", `btn-${variant}`, size === "sm" ? "btn-sm" : "", className]
    .filter(Boolean)
    .join(" ");

  return (
    <button type={type} className={classes} disabled={disabled} onClick={onClick}>
      {children}
    </button>
  );
}
