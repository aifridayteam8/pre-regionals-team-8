export default function Card({ title, actions, children, flush = false, className = "" }) {
  const classes = ["card", flush ? "card-flush" : "", className].filter(Boolean).join(" ");

  return (
    <section className={classes}>
      {(title || actions) && (
        <div className="card-head">
          {title && <h3 className="card-title">{title}</h3>}
          {actions && <div className="card-actions">{actions}</div>}
        </div>
      )}

      <div className="card-body">{children}</div>
    </section>
  );
}
