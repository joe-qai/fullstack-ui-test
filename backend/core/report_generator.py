from typing import Dict, List


class ReportGenerator:
    def __init__(self, task_data: Dict, results: List[Dict], logs: List[Dict]):
        self.task_data = task_data
        self.results = results
        self.logs = logs

    def generate_html(self) -> str:
        passed = sum(1 for r in self.results if r.get('status') in ('passed', 'success'))
        failed = sum(1 for r in self.results if r.get('status') in ('failed', 'error'))
        total = len(self.results)
        status_class = 'passed' if failed == 0 else 'failed'
        status_text = self.task_data.get('status', 'N/A')
        task_name = self.task_data.get('name', 'Unknown')
        created_at = self.task_data.get('created_at', 'N/A')

        result_rows = ''
        for r in self.results:
            s = r.get('status', 'N/A')
            s_class = 'passed' if s in ('passed', 'success') else 'failed'
            result_rows += (
                f"<tr><td>{r.get('device_id', 'N/A')}</td>"
                f"<td class=\"{s_class}\">{s}</td>"
                f"<td>{r.get('start_time', 'N/A')}</td>"
                f"<td>{r.get('end_time', 'N/A')}</td></tr>"
            )

        log_entries = ''
        for log in self.logs:
            ts = log.get('timestamp', '')
            level = log.get('level', 'INFO')
            msg = log.get('message', '')
            log_entries += f"<div class='log-entry'><span class='log-ts'>[{ts}]</span> <span class='log-level log-{level.lower()}'>{level}</span>: {msg}</div>"

        html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>测试报告 - {task_name}</title>
<style>
body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 40px; background: #f9f9f9; }}
.container {{ max-width: 1200px; margin: 0 auto; }}
h1 {{ color: #1a1a1a; border-bottom: 2px solid #1890ff; padding-bottom: 12px; }}
.summary {{ background: #fff; padding: 24px; border-radius: 8px; margin-bottom: 24px; box-shadow: 0 1px 4px rgba(0,0,0,0.08); }}
.summary-grid {{ display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 16px; margin-top: 16px; }}
.summary-item {{ text-align: center; padding: 16px; border-radius: 6px; background: #fafafa; }}
.summary-item .number {{ font-size: 36px; font-weight: 700; }}
.summary-item .label {{ font-size: 13px; color: #888; margin-top: 4px; }}
.passed {{ color: #52c41a; }} .failed {{ color: #ff4d4f; }}
table {{ width: 100%; border-collapse: collapse; margin-top: 16px; background: #fff; border-radius: 8px; overflow: hidden; box-shadow: 0 1px 4px rgba(0,0,0,0.08); }}
th, td {{ padding: 12px 16px; text-align: left; border-bottom: 1px solid #f0f0f0; }}
th {{ background: #fafafa; font-weight: 600; color: #555; }}
tr:hover td {{ background: #f5f9ff; }}
.log-section {{ background: #1e1e1e; color: #d4d4d4; padding: 16px; border-radius: 8px; max-height: 500px; overflow-y: auto; font-family: 'Cascadia Code', 'Fira Code', monospace; font-size: 12px; line-height: 1.6; margin-top: 16px; box-shadow: 0 1px 4px rgba(0,0,0,0.08); }}
.log-entry {{ padding: 2px 0; }}
.log-ts {{ color: #6a9955; }}
.log-level {{ font-weight: 600; }}
.log-info {{ color: #569cd6; }}
.log-warning {{ color: #ce9178; }}
.log-error {{ color: #f44747; }}
.step {{ margin: 8px 0; padding: 8px 12px; border-left: 3px solid #1890ff; background: #f6f8fa; border-radius: 0 4px 4px 0; }}
.step-failed {{ border-left-color: #ff4d4f; background: #fff2f0; }}
.step-passed {{ border-left-color: #52c41a; background: #f6ffed; }}
</style>
</head>
<body>
<div class="container">
<h1>测试报告</h1>
<div class="summary">
  <h2 style="margin: 0 0 4px 0;">执行概览</h2>
  <p style="color: #888; margin: 0 0 16px 0;">{task_name} | {created_at}</p>
  <div class="summary-grid">
    <div class="summary-item">
      <div class="number" style="color:#1890ff;">{total}</div>
      <div class="label">设备总数</div>
    </div>
    <div class="summary-item">
      <div class="number passed">{passed}</div>
      <div class="label">通过</div>
    </div>
    <div class="summary-item">
      <div class="number failed">{failed}</div>
      <div class="label">失败</div>
    </div>
  </div>
  <p style="margin-top: 16px;">任务状态: <strong class="{status_class}">{status_text}</strong></p>
</div>
<h3>设备结果</h3>
<table>
<tr><th>设备</th><th>状态</th><th>开始时间</th><th>结束时间</th></tr>
{result_rows}
</table>
<h3>执行日志</h3>
<div class="log-section">
{log_entries}
</div>
</div>
</body>
</html>"""
        return html

    def generate_pdf(self) -> bytes:
        from weasyprint import HTML
        html_content = self.generate_html()
        pdf_bytes = HTML(string=html_content).write_pdf()
        return pdf_bytes
