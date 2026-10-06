"""Losslessly package successful C jobs; retain all raw attempts, never use B XML."""
import collections,gzip,xml.etree.ElementTree as ET
from environment import *
def main():
    inventory={};packed=[]
    for name in ('jgrapht','spring-core'):
        campaign=read(OUT/'pit'/name/'campaign.json');assert campaign['completed']
        classes=[]
        for spec in read(ROOT/name/'config/sample_classes.json')['classes']:
            jobs=[r for r in campaign['jobs'] if r['fqn']==spec['fqn']];assert jobs
            usable=[r for r in jobs if r['status']=='OK'];assert len(usable)<=1
            row={'fqn':spec['fqn'],'targetTests':spec['targetTests'],'attempts':jobs,'status':jobs[-1]['status']}
            if usable:
                source=ROOT/usable[0]['directory']/'per-class'/spec['fqn']/'mutations.xml'
                target=OUT/'pit'/name/'per-class'/spec['fqn']/'mutations.xml.gz'
                raw=source.read_bytes();nodes=ET.fromstring(raw).findall('mutation')
                assert nodes and all(n.findtext('mutatedClass')==spec['fqn'] for n in nodes)
                ops=collections.Counter(n.findtext('mutator') for n in nodes);assert not any('NegateConditionalsMutator' in k for k in ops)
                target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(gzip.compress(raw,mtime=0))
                assert gzip.decompress(target.read_bytes())==raw
                item={'source':str(source.relative_to(ROOT)),'sourceSha256':sha(source),'packaged':str(target.relative_to(ROOT)),'packagedSha256':sha(target),'lossless':True};packed.append(item)
                row.update(matrix=item['packaged'],mutations=len(nodes),killed=sum(n.get('status')=='KILLED' for n in nodes),mutatorCounts=dict(ops),statusCounts=dict(collections.Counter(n.get('status') for n in nodes)))
            classes.append(row)
        inventory[name]={'sampledClasses':len(classes),'completeClasses':sum(r['status']=='OK' for r in classes),'classes':classes,'failedOrTimedOut':[r['fqn'] for r in classes if r['status']!='OK'],'campaign':campaign}
    write(OUT/'campaign_inventory.json',inventory);write(OUT/'matrix_packaging.json',packed)
    print({n:(d['sampledClasses'],d['completeClasses']) for n,d in inventory.items()})
if __name__=='__main__':main()
