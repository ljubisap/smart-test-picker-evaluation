"""Correct the implicit CLI operator fallback to the already-declared DEFAULTS policy.

The original runner is imported unchanged. Exactly one command option is added.
All unsuccessful default-resolution evidence is archived before the retry.
"""
import datetime,hashlib,importlib.util,json,shutil,subprocess,sys,tarfile,time
from pathlib import Path
from run_campaigns import ROOT,OUT,ENV,dump

def main():
 archive=OUT/'attempts/implicit-defaults.tar.gz';archive.parent.mkdir(exist_ok=True)
 if archive.exists():raise RuntimeError('Explicit-default retry already started; do not repeat automatically')
 paths=['results','java','scripts','pit/spring-core','matrix_packaging.json','campaign_inventory.json','comparison.json','COMPARISON.md','manuscript_comparison.json','MANUSCRIPT_COMPARISON.md','causal_review.json','causal_source_evidence.json','causal_guard_evidence.json','verification/unified.log']
 with tarfile.open(archive,'w:gz') as tar:
  for name in paths:
   if (OUT/name).exists():tar.add(OUT/name,arcname=name)
 dump(OUT/'attempts/implicit-defaults.json',{'archive':str(archive.relative_to(ROOT)),'sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'status':'REJECTED_NOT_UNIFIED','reason':'Unspecified CLI mutator list uses Mutator.newDefaults(), which includes NegateConditionals. Explicit DEFAULTS resolves through StandardMutatorGroups and uses RemoveConditionals.','verifierEvidence':'verification/unified.log in archive','retryClassification':'Declared-policy configuration correction, not a retry of a mutant to improve its status.'})
 previous=OUT/'pit/spring-core-implicit-defaults';directory=OUT/'pit/spring-core';shutil.move(str(directory),str(previous));directory.mkdir()
 for name in ('runtime-prerequisites.json','runtime-prerequisites.log'):
  shutil.copy2(previous/name,directory/name)
 checkout=Path(json.loads((OUT/'preflight.json').read_text())['subjects']['spring-core']['checkout'])
 cp=Path.home()/'.m2/repository/org/pitest';proof=OUT/'pit-default-resolution';proof.mkdir(exist_ok=True)
 javap='/Library/Java/JavaVirtualMachines/sapmachine-21.jdk/Contents/Home/bin/javap'
 for artifact,cls in [('pitest-command-line','org.pitest.mutationtest.commandline.OptionsParser'),('pitest','org.pitest.mutationtest.engine.gregor.config.GregorEngineFactory'),('pitest','org.pitest.mutationtest.engine.gregor.config.Mutator'),('pitest','org.pitest.mutationtest.engine.gregor.config.StandardMutatorGroups')]:
  cmd=[javap,'-c','-p','-classpath',str(cp/artifact/'1.17.4'/(artifact+'-1.17.4.jar')),cls]
  result=subprocess.run(cmd,text=True,capture_output=True,check=True);(proof/(cls.rsplit('.',1)[-1]+'.txt')).write_text(result.stdout)
 spec=importlib.util.spec_from_file_location('original_spring',ROOT/'spring-core/scripts/02_run_pit.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
 native=subprocess.run;calls=[]
 def logged(cmd,*a,**kw):
  original=list(map(str,cmd));effective=original
  if 'org.pitest.mutationtest.commandline.MutationCoverageReport' in original:
   assert '--mutators' not in original
   effective=original+['--mutators','DEFAULTS']
  row={'originalCommand':original,'command':effective,'cwd':str(kw.get('cwd',checkout)),'timeout':kw.get('timeout'),'startedUtc':datetime.datetime.now(datetime.timezone.utc).isoformat()};calls.append(row);start=time.monotonic()
  try:r=native(effective,*a,**kw);row['exitCode']=r.returncode;return r
  except subprocess.TimeoutExpired:row['status']='TIMEOUT';raise
  finally:row['elapsedSeconds']=time.monotonic()-start;dump(directory/'commands.json',calls)
 subprocess.run=logged;start=time.monotonic();status=0
 try:
  sys.argv=[str(ROOT/'spring-core/scripts/02_run_pit.py'),'--project-dir',str(checkout),'--results-dir',str(directory)];module.main()
 except SystemExit as exc:status=exc.code or 0
 finally:subprocess.run=native
 record={'subject':'spring-core','checkout':str(checkout),'exitCode':status,'elapsedSeconds':time.monotonic()-start,'commands':calls,'originalRunner':'spring-core/scripts/02_run_pit.py','runnerModified':False,'commandAdapter':['--mutators','DEFAULTS'],'reason':'Enforce the predeclared named DEFAULTS group, not the older empty-list CLI fallback.','previousAttempts':['pit/spring-core-initial-interrupted','pit/spring-core-implicit-defaults'],'maxRetriesUsedForInitiallyAttemptedClasses':2}
 dump(directory/'campaign.json',record);dump(OUT/'campaigns.json',[json.loads((OUT/'pit/jgrapht/campaign.json').read_text()),record]);(directory/'checkout-build.diff').write_text(subprocess.check_output(['git','diff'],cwd=checkout,text=True))
 print('EXPLICIT DEFAULTS CAMPAIGN FINISHED',status,flush=True)
if __name__=='__main__':main()
