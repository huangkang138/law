"""法源同步、健康检查与人工复核的内部 Flask CLI。"""

from __future__ import annotations

import json

import click

from .facade import LegalAgentFacade


def register_authority_commands(app) -> None:
    """注册可由计划任务和受控运维人员调用的法源命令。"""

    @app.cli.group("authority")
    def authority_group():
        """管理可信法律来源。"""

    @authority_group.command("sync")
    @click.option("--actor", default="scheduler", show_default=True, help="同步执行者标识。")
    def sync_command(actor: str):
        """从白名单官网同步法源；失败时返回非零退出码。"""
        facade = LegalAgentFacade()
        try:
            authorities = facade.import_official_labor_authorities(
                trigger="scheduled",
                requested_by=actor,
            )
        except Exception as exc:
            raise click.ClickException(f"法源同步失败: {type(exc).__name__}") from exc
        health = facade.get_authority_health()
        _echo({
            "ok": health["status"] == "ready",
            "count": len(authorities),
            "authorities": authorities,
            "health": health,
        })
        if health["status"] != "ready":
            raise click.ClickException(f"法源同步后状态为 {health['status']}")

    @authority_group.command("health")
    @click.option("--strict", is_flag=True, help="状态不是 ready 时返回非零退出码。")
    def health_command(strict: bool):
        """输出来源覆盖、新鲜度、待复核和最近同步状态。"""
        health = LegalAgentFacade().get_authority_health()
        _echo(health)
        if strict and health["status"] != "ready":
            raise click.ClickException(f"法源状态为 {health['status']}")

    @authority_group.command("pending")
    def pending_command():
        """列出正文变化后等待人工复核的版本。"""
        rows = LegalAgentFacade().list_pending_authority_reviews()
        _echo({"count": len(rows), "reviews": rows})

    @authority_group.command("review")
    @click.argument("authority_id")
    @click.option(
        "--decision",
        type=click.Choice(["approve", "reject"], case_sensitive=False),
        required=True,
    )
    @click.option("--reviewer", required=True, help="复核人内部标识。")
    @click.option("--notes", help="复核说明；驳回时必填。")
    def review_command(
        authority_id: str,
        decision: str,
        reviewer: str,
        notes: str | None,
    ):
        """批准或驳回待复核版本，并写入不可变审计记录。"""
        try:
            result = LegalAgentFacade().review_authority_version(
                authority_id,
                decision.lower(),
                reviewer,
                notes,
            )
        except Exception as exc:
            raise click.ClickException(str(exc)) from exc
        _echo(result)


def _echo(payload: dict) -> None:
    click.echo(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
