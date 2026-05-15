<task>
你是长篇网文连载质量评审。请只基于输入评审包，独立判断“久久端点一次性批量生成 3/5/7/10 章”在中文长篇创作中的稳定性。
重点不是润色文本，而是找批量生成导致的跑题、回环、误判、题材稀释和章节质量下滑。
</task>

<input>
{{INPUT_CONTENT}}
</input>

<dimensions>
- 批次稳定性: 3/5/7/10 哪个批次开始明显变差。
- 题材锁定: 玄幻黑暗、规则怪谈、末日、多子多福是否都持续存在，哪些被稀释。
- 长篇连续性: 是否出现重新开篇、重复醒来、主线回环、人物/资源/伏笔遗忘。
- 章节质量: 字数、冲突推进、场景新鲜度、节奏、信息密度。
- 生产建议: 推荐一次生成几章，是否需要批后总结/审稿/状态刷新。
</dimensions>

<structured_output_contract>
先给一句总判断。
然后输出表格: severity | evidence | issue | recommendation。
最后给出明确建议: recommended_batch_size、upper_bound、must_have_checks。
severity 只用 高/中/低。每条 evidence 必须指向具体批次或章节号。
</structured_output_contract>
