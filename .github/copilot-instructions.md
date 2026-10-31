# Brightloop workspace instructions

- Treat `MEMZO_PROJECT_CONTEXT.md` as the authoritative product specification.
- Preserve the Brightloop business scenario, one shared SQLite database, and the Admin, Staff, and Customer roles.
- Keep Flask, Flask-SQLAlchemy, Flask-Login, Werkzeug password hashing, HTML, CSS, and JavaScript as the core stack.
- Enforce role permissions and customer record ownership in backend routes; never trust hidden or disabled UI controls as authorization.
- Keep passwords hashed, validate inputs, use CSRF tokens on state-changing forms, and avoid hardcoded product or plan data.
- Keep public pages and role-specific dashboards separate while reusing the shared visual system.
- Favor a responsive, minimal, polished SaaS interface with clear spacing and restrained colors.
- Test changed workflows with the Flask test client and verify Python compilation before considering a feature complete.
- Run locally with `python app.py`; see `README.md` for setup, admin bootstrap, password reset email, and renewal maintenance details.
