"""CLI for exemption mgmt, sessions, reconcile, violations."""
import click
import sqlite3
from lpt.db import connect
from lpt.exemptions import add_exemption, remove_exemption, list_exemptions
from lpt.sessions import list_open_sessions
from lpt.violations import reconcile_open, check_and_record
import yaml

DEFAULT_DB = "parking.db"
DEFAULT_CONFIG = "config.yaml"


def _cfg():
    with open(DEFAULT_CONFIG) as f:
        return yaml.safe_load(f)


def _conn():
    return connect(DEFAULT_DB)


@click.group()
def cli():
    pass


@cli.group()
def exempt():
    pass


@exempt.command("add")
@click.argument("plate")
@click.option("--reason", default=None)
@click.option("--expires", default=None)
def exempt_add(plate, reason, expires):
    conn = _conn()
    add_exemption(conn, plate, reason, expires)
    click.echo(f"Exempted {plate}")


@exempt.command("remove")
@click.argument("plate")
def exempt_remove(plate):
    conn = _conn()
    remove_exemption(conn, plate)
    click.echo(f"Removed {plate}")


@exempt.command("list")
def exempt_list():
    conn = _conn()
    for e in list_exemptions(conn):
        click.echo(e)


@cli.command("sessions")
@click.option("--open", "only_open", is_flag=True)
def sessions_cmd(only_open):
    conn = _conn()
    if only_open:
        for s in list_open_sessions(conn):
            click.echo(s)
    else:
        for r in conn.execute("SELECT * FROM sessions ORDER BY entry_time DESC").fetchall():
            click.echo(dict(r))


@cli.command("reconcile")
def reconcile_cmd():
    cfg = _cfg()
    conn = _conn()
    cands = reconcile_open(conn, cfg["max_stay_minutes"])
    for c in cands:
        click.echo(c)
        if click.confirm("Mark as violation?"):
            # build session dict
            sess = {"id": c["id"], "plate": c["plate"], "duration_min": c["duration_min"]}
            check_and_record(conn, sess, cfg["max_stay_minutes"])


@cli.command("violations")
def violations_cmd():
    conn = _conn()
    for r in conn.execute("SELECT * FROM violations ORDER BY notified_at DESC").fetchall():
        click.echo(dict(r))


if __name__ == "__main__":
    cli()
