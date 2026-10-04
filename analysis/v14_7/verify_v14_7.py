#!/usr/bin/env python3
"""Recompute and verify the three v14.7 analysis outputs."""
import argparse, importlib.util, json, tempfile
from pathlib import Path

HERE=Path(__file__).resolve().parent
def main():
 parser=argparse.ArgumentParser(); parser.add_argument('--verify',action='store_true',required=True); parser.parse_args()
 spec=importlib.util.spec_from_file_location('v147_checks',HERE/'run_checks.py'); module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
 names=['springcore_run2_sensitivity.json','worked_example_v14_6.json','test_segment_v14_6.json']; expected={n:json.loads((HERE/n).read_text()) for n in names}
 with tempfile.TemporaryDirectory(prefix='verify-v14-7-') as tmp:
  module.OUT=Path(tmp); module.OUT.mkdir(parents=True,exist_ok=True)
  module.sensitivity(); module.worked_example(); module.segment_scan()
  errors=[n for n in names if json.loads((module.OUT/n).read_text())!=expected[n]]
 if errors: raise SystemExit('VERIFY FAILED: '+', '.join(errors))
 print('VERIFY PASSED: v14.7 spring-core sensitivity, worked example, and eight-subject test-segment scan match inputs')
if __name__=='__main__': main()
