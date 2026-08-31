# Dependencias y auditoría (OWASP A06)

## Auditoría local

```bash
pip install pip-audit
pip-audit
```

CI ejecuta `pip-audit` como advisory (non-blocking).

## Actualización

```bash
pip install -e ".[dev]" --upgrade
pytest
```

## Pinning

Versiones mínimas en [`pyproject.toml`](../pyproject.toml). Para producción, generar lockfile periódico.

## Reporte de vulnerabilidad

Usar [`.github/ISSUE_TEMPLATE/bug_report.md`](../.github/ISSUE_TEMPLATE/bug_report.md) con etiqueta `security`.
