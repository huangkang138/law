-- PostgreSQL 表中文注释。
-- 如业务表不在 public schema，只需修改 target_schema。

DO $$
DECLARE
    target_schema text := 'public';
    item record;
BEGIN
    FOR item IN
        SELECT *
        FROM (VALUES
            ('alembic_version', 'Alembic 数据库迁移版本标记'),
            ('users', '用户账号与基础身份信息'),
            ('contracts', '上传合同的文件信息、正文与摘要'),
            ('contract_risks', '合同条款风险识别与修改建议'),
            ('legal_chat_sessions', '普法问答会话'),
            ('legal_chat_messages', '普法问答会话消息'),
            ('cases', '模拟庭审案件基础信息'),
            ('court_sessions', '模拟庭审会话与裁判结果'),
            ('evidence', '模拟庭审案件证据'),
            ('legal_issues', '案件法律争议焦点'),
            ('debate_turns', '模拟庭审各方发言回合'),
            ('case_analyses', '案情分析与推断记录'),
            ('similar_document_searches', '相似法律文书检索记录'),
            ('dispute_infos', '纠纷事实整理结果'),
            ('evidence_records', '纠纷取证与存证记录'),
            ('rights_protection_paths', '纠纷维权路径规划结果'),
            ('legal_documents', '已生成的法律文书'),
            ('case_predictions', '同类案件结果预判记录'),
            ('case_reminders', '案件流程与期限提醒'),
            ('risk_warnings', '纠纷处理风险提醒'),
            ('legal_cases', '法律案例库'),
            ('case_explanation_searches', '相似案例解释检索记录'),
            ('document_drafts', '通用文档起草任务'),
            ('contract_draft_messages', '合同起草过程中的对话消息'),
            ('legal_document_drafts', '法律文书起草详情'),
            ('legal_document_draft_messages', '法律文书起草过程中的对话消息'),
            ('contract_drafts', '合同起草详情'),
            ('legal_opinion_drafts', '法律意见书起草详情'),
            ('legal_opinion_draft_messages', '法律意见书起草过程中的对话消息'),
            ('interest_calculations', '利息计算记录'),
            ('labor_compensations', '劳动补偿计算记录'),
            ('traffic_accident_compensations', '交通事故赔偿计算记录'),
            ('court_fees', '诉讼费用计算记录'),
            ('work_injury_compensations', '工伤赔偿计算记录'),
            ('lawyer_fees', '律师费用估算记录'),
            ('legal_calendar_events', '法律日历事件与期限'),
            ('limitation_checks', '诉讼时效查询记录'),
            ('contract_penalties', '合同违约金计算记录'),
            ('preservation_fees', '财产保全费计算记录'),
            ('execution_fees', '强制执行费计算记录'),
            ('will_fees', '遗嘱相关费用计算记录'),
            ('announcement_fees', '公告费计算记录'),
            ('appraisal_fees', '鉴定费计算记录'),
            ('arbitration_fees', '仲裁费计算记录'),
            ('uml_diagrams', 'UML 图表生成记录'),
            ('favorites', '用户收藏内容'),
            ('agents', '可用智能体配置'),
            ('agent_usages', '智能体调用与用量记录'),
            ('digital_human_sessions', '数字人对话会话'),
            ('digital_human_messages', '数字人会话原始消息'),
            ('conversation_memories', '数字人会话结构化记忆与滚动摘要'),
            ('digital_human_requests', '数字人请求幂等、租约与恢复检查点'),
            ('matters', '法律 Agent 案件工作区'),
            ('agent_runs', '法律 Agent 可暂停恢复的运行实例'),
            ('agent_steps', 'Agent 运行中的持久化计划步骤'),
            ('tool_calls', '受控工具调用及结构化结果'),
            ('approval_requests', '需用户确认的高风险操作审批'),
            ('agent_audit_events', 'Agent 状态变更审计事件'),
            ('matter_jurisdictions', '案件候选及已确认法域'),
            ('agent_documents', '案件工作区授权材料元数据'),
            ('document_fragments', '带页码或字符位置的材料片段'),
            ('legal_facts', '从材料提取且带出处的结构化事实'),
            ('legal_authorities', '带法域、版本和有效期的法律来源'),
            ('labor_dispute_profiles', '劳动纠纷结构化事实与流程状态'),
            ('agent_artifacts', 'Agent 生成的可审阅交付物'),
            ('knowledge_graphs', '法律知识图谱'),
            ('knowledge_graph_nodes', '旧版法律知识图谱层级节点'),
            ('knowledge_graph_edges', '旧版法律知识图谱节点连边'),
            ('knowledge_nodes', '法律知识图谱节点'),
            ('knowledge_references', '旧版法律知识节点引用来源'),
            ('knowledge_relations', '旧版法律知识节点语义关系'),
            ('knowledge_relationships', '法律知识图谱节点关系'),
            ('matter_fact_assertions', '案件事实的版本化断言'),
            ('agent_plans', 'Agent 运行的版本化执行计划'),
            ('agent_run_actions', 'Agent 运行幂等动作记录'),
            ('agent_event_outbox', 'Agent 领域事件发件箱'),
            ('authority_sync_runs', '官方法源同步运行记录'),
            ('authority_source_snapshots', '官方法源原始响应快照'),
            ('authority_source_reviews', '法源正文变化人工复核记录'),
            ('labor_case_triages', '案件劳动争议分流事实与判断结果')
        ) AS comments(table_name, comment_text)
    LOOP
        IF to_regclass(format('%I.%I', target_schema, item.table_name)) IS NULL THEN
            RAISE NOTICE '跳过不存在的表：%.%', target_schema, item.table_name;
        ELSE
            EXECUTE format(
                'COMMENT ON TABLE %I.%I IS %L',
                target_schema,
                item.table_name,
                item.comment_text
            );
        END IF;
    END LOOP;
END
$$;

-- 执行完成后查看全部业务表及其中文注释。
SELECT
    schemaname AS "模式",
    tablename AS "表名",
    obj_description(
        format('%I.%I', schemaname, tablename)::regclass,
        'pg_class'
    ) AS "表注释"
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY tablename;
