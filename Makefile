# claude-verified-agent — 1-command demo, tests, gates.
# Local: uses ~/ai_env/bin/python when present (pillars pre-installed).
# CI: falls back to python3.

PYTHON := $(shell if [ -x $(HOME)/ai_env/bin/python ]; then echo $(HOME)/ai_env/bin/python; else echo python3; fi)

.PHONY: demo test eval gates pillars all clean

pillars:
	$(PYTHON) -m pip install -e ".[pillars]" || echo "pillars unavailable offline, using stdlib fallback"

demo:
	$(PYTHON) demo/demo.py

test:
	$(PYTHON) -m pytest -v

eval: gates

gates:
	@for suite in evals/non_regression.json evals/schema.json evals/tripwires.json; do \
		if $(PYTHON) -c "import llm_eval" 2>/dev/null && command -v llm-eval >/dev/null 2>&1; then \
			echo "== llm-eval run $$suite"; \
			llm-eval run "$$suite" --report report.md --json report.json || exit 1; \
		else \
			echo "== fallback gate $$suite (llm-eval-ci not installed)"; \
			$(PYTHON) -m verified_agent.gates run "$$suite" || exit 1; \
		fi; \
	done

all: test gates demo

clean:
	rm -rf report.md report.json src/*.egg-info .pytest_cache tests/__pycache__ src/verified_agent/__pycache__ demo/__pycache__
	find . -name "__pycache__" -type d -prune -exec rm -rf {} + 2>/dev/null; true
