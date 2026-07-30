export default function Header({ eyebrow, title, subtitle, actions }) {
  return (
    <header className="page-header">
      <div className="page-header-text">
        {eyebrow && <p className="page-eyebrow">{eyebrow}</p>}
        <h1 className="page-title">{title}</h1>
        {subtitle && <p className="page-subtitle">{subtitle}</p>}
      </div>

      {actions && <div className="page-header-side">{actions}</div>}
    </header>
  );
}
